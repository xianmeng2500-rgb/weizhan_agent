"""AI 生成记录模型"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.database import Base


def _utcnow() -> datetime:
    """与现有模型一致的 UTC naive 时间"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AIGeneration(Base):
    """AI 生图记录表：保存每次生成的提示词、参考图与结果图 URL"""
    __tablename__ = "ai_generations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="生成者(后台用户ID)")
    prompt = Column(Text, nullable=False, comment="提示词")
    negative_prompt = Column(Text, nullable=True, comment="负面提示词")
    reference_image = Column(String(1000), nullable=True, comment="参考图URL(图生图)")
    result_url = Column(String(1000), nullable=False, comment="生成结果图URL")
    provider = Column(String(50), default="dashscope", nullable=False, comment="AI服务商")
    model_name = Column(String(100), default="wanx2.1-t2i-turbo", nullable=False, comment="模型名称")
    size = Column(String(30), default="1024*1024", nullable=False, comment="生成尺寸")
    created_at = Column(DateTime, default=_utcnow, comment="生成时间")
