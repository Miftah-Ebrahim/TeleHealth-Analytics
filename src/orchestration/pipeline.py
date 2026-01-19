import subprocess
import os
from dagster import op, job, logger


@op
def scrape_telegram():
    """Run the Telegram scraper script."""
    logger.info("Starting Telegram Scrape...")
    subprocess.run(["python", "src/collectors/telegram_scraper.py"], check=True)
    logger.info("Telegram Scrape Complete.")


@op
def load_data(start_after_scrape):
    """Run the Postgres loader script. Depends on scrape completion."""
    logger.info("Starting Postgres Load...")
    subprocess.run(["python", "src/loaders/postgres_loader.py"], check=True)
    logger.info("Postgres Load Complete.")


@op
def enrich_data(start_after_load):
    """Run the YOLO enrichment script. Depends on data load (image availability)."""
    logger.info("Starting AI Enrichment...")
    # Enrichment reads images (from scraper) and writes CSV/DB
    subprocess.run(["python", "src/enrichment/yolo_detect.py"], check=True)
    logger.info("AI Enrichment Complete.")


@op
def transform_data(start_after_enrich):
    """Run dbt transformations. Depends on enrichment (fact table source)."""
    logger.info("Starting dbt transformations...")
    # Assuming dbt is installed and available in path
    project_dir = "dbt_project"
    subprocess.run(["dbt", "build", "--project-dir", project_dir], check=True)
    logger.info("dbt Transformations Complete.")


@job
def telehealth_daily_pipeline():
    """
    Daily pipeline: Scrape -> Load -> Enrich (YOLO) -> Transform (dbt).
    Note: 'Load' loads JSONs. 'Enrich' processes images and loads detections.
    Ideally, Enrich and Load could be parallel after Scrape, but let's sequence for simplicity:
    Scrape -> Load (JSON) -> Enrich (Images + DB Load) -> Transform (dbt, uses both sources).
    """
    scraped = scrape_telegram()
    loaded = load_data(scraped)
    enriched = enrich_data(loaded)
    transform_data(enriched)
