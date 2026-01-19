import os
import pandas as pd
from ultralytics import YOLO
import logging
from sqlalchemy import create_engine, text
import glob

import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from src.config import settings

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/yolo_detect.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Database Credentials
DB_CONNECTION_STR = settings.DB_CONNECTION_STR


def detect_and_classify(image_path, model):
    """
    Runs YOLO detection and classifies the image based on rubric rules.
    """
    try:
        results = model(image_path)
        result = results[0]

        detected_classes = [result.names[int(cls)] for cls in result.boxes.cls]
        confidence_scores = [float(conf) for conf in result.boxes.conf]

        # Taking the highest confidence detection for simplicity in main reporting
        # or joining all detections. The requirements imply a single classification per image.

        # Classification Logic
        has_person = "person" in detected_classes
        has_bottle = "bottle" in detected_classes
        has_cup = "cup" in detected_classes

        image_category = "other"
        if has_person and has_bottle:
            image_category = "promotional"
        elif (has_bottle or has_cup) and not has_person:
            image_category = "product_display"

        # Join classes and mean confidence for record
        primary_class = detected_classes[0] if detected_classes else "none"
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores
            else 0.0
        )

        return {
            "detected_class": primary_class,
            "confidence": avg_confidence,
            "image_category": image_category,
            "all_classes": ", ".join(detected_classes),
        }

    except Exception as e:
        logger.error(f"Error processing {image_path}: {e}")
        return None


def main():
    logger.info("Starting AI Enrichment Process...")

    # Load Model (Nano)
    try:
        model = YOLO("yolov8n.pt")
    except Exception as e:
        logger.error(f"Failed to load YOLO model: {e}")
        return

    # Find Images
    image_dir = "data/raw/images"
    image_paths = glob.glob(os.path.join(image_dir, "**", "*.jpg"), recursive=True)

    if not image_paths:
        logger.warning("No images found to process.")
        return

    results_data = []

    for img_path in image_paths:
        # Extract message_id and channel from path
        # Expected path: data/raw/images/{channel}/{message_id}.jpg
        try:
            parts = img_path.replace("\\", "/").split("/")
            message_id = parts[-1].replace(".jpg", "")
            channel_name = parts[-2]

            detection = detect_and_classify(img_path, model)

            if detection:
                record = {
                    "message_id": message_id,
                    "channel_name": channel_name,
                    **detection,
                    "image_path": img_path,
                }
                results_data.append(record)

        except Exception as e:
            logger.error(f"Skipping file due to path error {img_path}: {e}")

    # Save to CSV
    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "yolo_results.csv")

    df = pd.DataFrame(results_data)
    if not df.empty:
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved {len(df)} detection results to {csv_path}")

        # Load to Postgres
        try:
            engine = create_engine(DB_CONNECTION_STR)

            # Create schema 'raw' if needed (though loader likely did it)
            # We will use 'raw_image_detections' table in 'public' or 'raw' schema?
            # User said: "Postgres table named raw_image_detections". Usually implies public or raw.
            # Let's put it in 'raw' to match other raw tables, or just public if unspecified.
            # Given dbt models usually source from something, and other table is raw.telegram_messages.
            # I will use 'raw' schema for consistency with the loader 'raw.telegram_messages'.

            table_name = "image_detections"
            schema = "raw"

            df.to_sql(
                table_name, engine, schema=schema, if_exists="replace", index=False
            )
            logger.info(f"Loaded data to {schema}.{table_name}")

        except Exception as e:
            logger.error(f"Database load failed: {e}")
    else:
        logger.warning("No detections to save.")


if __name__ == "__main__":
    main()
