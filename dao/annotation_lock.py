# -*- coding: utf-8 -*-
"""annotation_lock 表：记录当前正在编辑的 BUC 图片锁。"""

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint

from dao.database import Base, beijing_now, format_beijing_time

# 注册外键引用表到同一个 Base.metadata。
from dao import user_account  # noqa: F401


class AnnotationLock(Base):
    """一张 BUC/func 图片最多只有一个有效编辑锁。"""

    __tablename__ = "annotation_lock"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    buc = Column(String(10), nullable=False)
    func = Column(String(255), nullable=False)
    locked_by = Column(Integer, ForeignKey("user_account.id"), nullable=False)
    locked_session_id = Column(String(64), nullable=False)
    locked_at = Column(DateTime, nullable=False, default=beijing_now)

    __table_args__ = (
        UniqueConstraint("buc", "func", name="uq_annotation_lock_buc_func"),
        Index("idx_annotation_lock_user_session", "locked_by", "locked_session_id"),
        Index("idx_annotation_lock_time", "locked_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "buc": self.buc,
            "func": self.func,
            "locked_by": self.locked_by,
            "locked_session_id": self.locked_session_id,
            "locked_at": format_beijing_time(self.locked_at),
        }
