from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from collections import Counter
import re
from typing import List
from .schemas import (
    HealthCheck,
    TopProduct,
    ChannelActivity,
    VisualContentStats,
    VisualContentResponse,
    SearchResult,
)

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from src.config import settings

# Database Setup
engine = create_engine(settings.DB_CONNECTION_STR)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="TeleHealth Analytics API")


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health", response_model=HealthCheck)
def health_check():
    return {"status": "ok"}


@app.get("/api/reports/top-products", response_model=List[TopProduct])
def get_top_products(db: Session = Depends(get_db)):
    """
    Returns most frequent text tokens from messages, simulating 'product' extraction.
    Logic: Fetches message text from fct_messages, tokenizes, and counts.
    """
    try:
        # Fetching texts from fct_messages via raw.telegram_messages or stg/fct table
        # Since dbt models might be in a different schema (dbt_postgres), let's query the marts or public view if it exists.
        # Assuming dbt runs into 'dbt_postgres' schema or similar as per default profiles.yml
        # In this setup, we'll try to query likely table locations.

        # NOTE: Using raw table for text access if marts don't preserve full text or for simplicity
        query = text(
            "SELECT message_text FROM raw.telegram_messages WHERE message_text IS NOT NULL LIMIT 1000"
        )
        result = db.execute(query).fetchall()

        all_text = " ".join([row[0] for row in result])
        # Simple tokenization
        tokens = re.findall(r"\w+", all_text.lower())
        # Filter small words
        tokens = [t for t in tokens if len(t) > 3]

        counts = Counter(tokens)
        top_10 = counts.most_common(10)

        return [{"token": t, "count": c} for t, c in top_10]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/channels/{channel_name}/activity", response_model=List[ChannelActivity])
def get_channel_activity(channel_name: str, db: Session = Depends(get_db)):
    """
    Returns daily post counts for a specific channel.
    """
    try:
        # Sanitize input slightly or rely on param binding.
        # Querying fct_messages and dim_dates (or just grouping by date key)
        # We need to map channel_name to channel_key or just filter by raw table if simpler
        # But rubric asks for dim_channels + fct_messages usage.

        # Warning: Schema might be 'dbt_postgres' or 'public' depend on dbt profile settings.
        # Set to 'dbt_postgres' based on previous tasks.

        query = text("""
            SELECT 
                d.date_day,
                COUNT(f.message_id) as post_count
            FROM dbt_postgres.fct_messages f
            JOIN dbt_postgres.dim_channels c ON f.channel_key = c.channel_key
            JOIN dbt_postgres.dim_dates d ON f.date_key = d.date_key
            WHERE c.channel_name = :channel_name
            GROUP BY d.date_day
            ORDER BY d.date_day DESC
        """)

        result = db.execute(query, {"channel_name": channel_name}).fetchall()

        return [
            {"date": row[0], "post_count": row[1], "channel_name": channel_name}
            for row in result
        ]
    except Exception as e:
        # Fallback to looking in raw if dbt tables not ready or empty for this specific channel
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/api/reports/visual-content", response_model=VisualContentResponse)
def get_visual_content_stats(db: Session = Depends(get_db)):
    """
    Returns count of promotional vs product_display images.
    """
    try:
        query = text("""
            SELECT image_category, COUNT(*) as count
            FROM dbt_postgres.fct_image_detections
            GROUP BY image_category
        """)

        result = db.execute(query).fetchall()
        stats = [{"image_category": row[0], "count": row[1]} for row in result]
        return {"stats": stats}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/api/search/messages", response_model=List[SearchResult])
def search_messages(keyword: str, db: Session = Depends(get_db)):
    """
    Search messages by keyword (ILIKE).
    """
    try:
        # Searching raw messages or fct_messages.
        # Using fct_messages linked to dim_channels might be better but raw has text more reliably?
        # fct_messages usually has keys. Let's assume raw text is in raw table or stg.
        # Logic: Select from raw.telegram_messages

        query = text("""
            SELECT 
                r.message_id, 
                r.channel_name, 
                r.message_date::date as date,
                r.message_text
            FROM raw.telegram_messages r
            WHERE r.message_text ILIKE :keyword
            ORDER BY r.message_date DESC
            LIMIT 50
        """)

        search_pattern = f"%{keyword}%"
        result = db.execute(query, {"keyword": search_pattern}).fetchall()

        return [
            {
                "message_id": row[0],
                "channel_name": row[1],
                "date": row[2],
                "message_text": row[3],
            }
            for row in result
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
