import os
import json
import pandas as pd
import logging
import glob
from sqlalchemy import create_engine, text
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database Credentials
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "telehealth"
DB_USER = "user"
DB_PASSWORD = "password"

# Construct Connection String
DB_CONNECTION_STR = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def load_json_files(base_directory):
    """
    Recursively finds and reads all JSON files in the specified directory structure.
    Expected structure: data/raw/telegram_messages/YYYY-MM-DD/*.json
    """
    # Recursive glob pattern
    search_pattern = os.path.join(base_directory, "**", "*.json")
    json_files = glob.glob(search_pattern, recursive=True)

    if not json_files:
        logger.warning(
            f"No JSON files found in {base_directory} (recursively). Exiting gracefully."
        )
        return None

    all_data = []
    for file in json_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                elif isinstance(data, dict):
                    all_data.append(data)
            logger.info(f"Loaded data from {file}")
        except Exception as e:
            logger.error(f"Error reading {file}: {e}")

    return all_data


def clean_data(df):
    """
    Cleans the DataFrame: checks for required columns, converts dates, etc.
    """
    if df.empty:
        return df

    # Ensure 'message_date' is datetime
    if "message_date" in df.columns:
        df["message_date"] = pd.to_datetime(df["message_date"], errors="coerce")

    # Remove duplicates if 'message_id' and 'channel_name' exists
    if "message_id" in df.columns and "channel_name" in df.columns:
        df.drop_duplicates(subset=["message_id", "channel_name"], inplace=True)

    return df


def main():
    json_dir = "data/raw/telegram_messages"

    logger.info("Starting data loading process...")

    raw_data = load_json_files(json_dir)

    if not raw_data:
        return

    df = pd.DataFrame(raw_data)
    logger.info(f"Combined DataFrame created with {len(df)} records.")

    # Clean Data
    df = clean_data(df)

    # Load to Postgres
    try:
        engine = create_engine(DB_CONNECTION_STR)

        # Create schema 'raw' if it doesn't exist
        with engine.connect() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
            connection.commit()

        table_name = "telegram_messages"
        schema_name = "raw"

        logger.info(f"Writing data to table '{schema_name}.{table_name}'...")

        # Load data to raw.telegram_messages
        df.to_sql(
            table_name, engine, schema=schema_name, if_exists="replace", index=False
        )

        logger.info("Data loaded successfully.")

    except Exception as e:
        logger.error(f"Failed to write to database: {e}")


if __name__ == "__main__":
    main()
