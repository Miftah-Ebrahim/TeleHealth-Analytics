from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class HealthCheck(BaseModel):
    status: str


class TopProduct(BaseModel):
    token: str
    count: int


class ChannelActivity(BaseModel):
    date: date
    post_count: int
    channel_name: str


class VisualContentStats(BaseModel):
    image_category: str
    count: int


class VisualContentResponse(BaseModel):
    stats: List[VisualContentStats]


class SearchResult(BaseModel):
    message_id: int
    channel_name: str
    date: date
    message_text: str
