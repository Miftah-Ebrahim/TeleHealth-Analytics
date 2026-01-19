import os
import json
import asyncio
import logging
import random
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/scraper.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
API_ID = os.getenv("TG_API_ID")
API_HASH = os.getenv("TG_API_HASH")

CHANNELS = ["@lobelia4cosmetics", "@tikvahpharma", "@CheMed123"]
LIMIT = 100


async def scrape_channel(client, channel_username):
    """
    Scrapes messages from a single Telegram channel with enhanced fields and structure.
    """
    try:
        logger.info(f"Starting scrape for {channel_username}...")
        entity = await client.get_entity(channel_username)
        channel_title = entity.title

        # Date-based directory for JSONs
        today_date = datetime.now().strftime("%Y-%m-%d")
        json_dir = f"data/raw/telegram_messages/{today_date}"
        os.makedirs(json_dir, exist_ok=True)

        # Image directory
        clean_username = channel_username.strip("@")
        image_dir = f"data/raw/images/{clean_username}"
        os.makedirs(image_dir, exist_ok=True)

        messages_data = []
        message_count = 0

        async for message in client.iter_messages(entity, limit=LIMIT):
            # Extract common fields
            msg_id = message.id
            msg_date = message.date.isoformat() if message.date else None
            msg_text = message.message
            views = message.views if message.views else 0
            forwards = message.forwards if message.forwards else 0

            # Media handling
            has_media = False
            image_path = None

            if message.photo:
                has_media = True
                # Download image to specified path: data/raw/images/{channel}/{message_id}.jpg
                # Telethon download_media can take a specific file path
                target_img_path = os.path.join(image_dir, f"{msg_id}.jpg")

                # Check if already exists to save bandwidth/time (optional, but good practice)
                if not os.path.exists(target_img_path):
                    path = await message.download_media(file=target_img_path)
                    image_path = path
                else:
                    image_path = target_img_path

            msg_data = {
                "message_id": msg_id,
                "channel_name": clean_username,  # Using the username as unique identifier key usually better
                "channel_title": channel_title,  # Keeping title for context
                "message_date": msg_date,
                "message_text": msg_text,
                "has_media": has_media,
                "image_path": image_path,
                "views": views,
                "forwards": forwards,
            }

            messages_data.append(msg_data)
            message_count += 1

            # Politeness delay
            await asyncio.sleep(random.uniform(0.5, 1.0))

        # Save to JSON: data/raw/telegram_messages/YYYY-MM-DD/channel.json
        output_file = f"{json_dir}/{clean_username}.json"

        # If file exists, we might want to append or overwrite.
        # For simplicity and idempotency in this run, we overwrite with the latest batch.
        # In a real continuous scraper, we might load existing and append new IDs.
        # Given the task description implies a run-based scrape, overwriting the daily file for this run is acceptable.

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(messages_data, f, ensure_ascii=False, indent=4)

        logger.info(
            f"Successfully scraped {message_count} messages from {channel_username}. Saved to {output_file}."
        )

    except Exception as e:
        logger.error(f"Error scraping {channel_username}: {e}")


async def main():
    if not API_ID or not API_HASH:
        logger.critical("API_ID or API_HASH missing in .env file.")
        return

    logger.info("Initializing Telegram Client...")

    # 'anon' session file will be created in current directory
    async with TelegramClient("anon", API_ID, API_HASH) as client:
        for channel in CHANNELS:
            await scrape_channel(client, channel)


if __name__ == "__main__":
    asyncio.run(main())
