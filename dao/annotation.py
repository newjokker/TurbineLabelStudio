# -*- coding: utf-8 -*-
"""本地 annotation 表：BUC 图片与标注框主表。"""
import logging
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.exc import SQLAlchemyError

from dao.database import Base, Session, format_beijing_time, json_text, json_value
from dao.wav_buc import WavBuc

# 注册外键引用表到同一个 Base.metadata，避免单独导入本 DAO 时外键解析失败。
from dao import label, user_account  # noqa: F401


def utc_now():
    """返回去掉时区信息的 UTC 时间，保持 SQLite DateTime 存储简单。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Annotation(Base):
    """主表：记录 BUC 图片与标注框。"""

    __tablename__ = "annotation"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    buc = Column(String(10), nullable=False)
    func = Column(String(255), nullable=False)
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    label_id = Column(Integer, ForeignKey("label.id"), nullable=False)
    difficult = Column(Boolean, nullable=False, default=False)
    update_time = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    update_id = Column(Integer, ForeignKey("user_account.id"), nullable=False)
    update_reason = Column(String(500), nullable=False)
    extra_info = Column(Text, nullable=False, default="{}")

    __table_args__ = (
        CheckConstraint(
            "length(buc) = 10 AND buc GLOB 'BUC_[0-9][0-9][0-9][0-9][0-9][0-9]'",
            name="ck_annotation_buc_format",
        ),
        CheckConstraint(
            "length(func) > 0",
            name="ck_annotation_func_not_empty",
        ),
        Index("idx_annotation_buc", "buc"),
        Index("idx_annotation_buc_func", "buc", "func"),
        Index("idx_annotation_label_id", "label_id"),
        Index("idx_annotation_update_time", "update_time"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "buc": self.buc,
            "func": self.func,
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "label_id": self.label_id,
            "difficult": self.difficult,
            "update_time": format_beijing_time(self.update_time),
            "update_id": self.update_id,
            "update_reason": self.update_reason,
            "extra_info": json_value(self.extra_info),
        }


def add_annotation(
    buc,
    func,
    x1,
    y1,
    x2,
    y2,
    label_id,
    update_id,
    update_reason,
    difficult=False,
    extra_info=None,
):
    """添加主表标注记录。"""
    if not buc or not func or update_id is None or not update_reason:
        logging.error("添加标注记录失败 buc/func/update_id/update_reason 不能为空")
        return None

    session = Session()
    try:
        if not session.query(WavBuc.buc).filter_by(buc=buc).first():
            logging.error("添加标注记录失败 buc 不存在于 wav_buc 表 buc=%s", buc)
            return None

        record = Annotation(
            buc=buc,
            func=func,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            label_id=label_id,
            difficult=difficult,
            update_id=update_id,
            update_reason=update_reason,
            extra_info=json_text(extra_info),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record.to_dict()
    except SQLAlchemyError:
        session.rollback()
        logging.exception("添加标注记录失败 buc=%s func=%s label_id=%s", buc, func, label_id)
        return None
    finally:
        session.close()
