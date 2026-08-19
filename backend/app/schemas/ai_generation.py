"""AI 生成记录 Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AIGenerationOut(BaseModel):
    id: int
    prompt: str
    negative_prompt: Optional[str] = None
    reference_image: Optional[str] = None
    result_url: str
    provider: str
    model_name: str
    size: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedGenerations(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AIGenerationOut]
