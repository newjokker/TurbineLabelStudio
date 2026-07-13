# -*- coding: utf-8 -*-
"""user_permission 表：保存每个账号的细粒度权限覆盖值。"""

from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String, UniqueConstraint

from dao.database import Base

# 注册外键引用表到同一个 Base.metadata。
from dao import user_account  # noqa: F401


class UserPermission(Base):
    __tablename__ = "user_permission"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False)
    permission = Column(String(100), nullable=False)
    enabled = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint("user_id", "permission", name="uq_user_permission_user_key"),
        Index("idx_user_permission_user_id", "user_id"),
    )

    def to_dict(self):
        return {"user_id": self.user_id, "permission": self.permission, "enabled": bool(self.enabled)}
