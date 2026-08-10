"""表单提交记录模型"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.database import Base


class FormSubmission(Base):
    """模块报名表单提交记录"""
    __tablename__ = "form_submissions"
    __table_args__ = (
        Index(
            "uq_form_submission_logged_account",
            "site_id", "module_id", "account_id",
            unique=True,
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True, comment="所属微站")
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False, index=True, comment="所属模块")
    account_id = Column(Integer, ForeignKey("site_accounts.id"), nullable=True, comment="提交账号(登录用户)")
    submitter_name = Column(String(128), nullable=True, comment="提交者姓名")
    submitter_phone = Column(String(20), nullable=True, comment="提交者手机号")
    data = Column(JSON, nullable=False, comment="提交数据(JSON)")
    note = Column(Text, nullable=True, comment="备注/管理员备注")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="提交时间")

    # 关系
    site = relationship("Site", back_populates="form_submissions")
    module = relationship("Module", back_populates="form_submissions")
    account = relationship("SiteAccount", back_populates="form_submissions")
