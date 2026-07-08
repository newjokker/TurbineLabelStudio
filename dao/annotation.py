# -*- coding: utf-8 -*-
"""本地 annotation 表：UC 与标注框主表。"""
import logging

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.exc import SQLAlchemyError

from dao.database import Base, Session, beijing_now, format_beijing_time, json_text, json_value


class Annotation(Base):
    """主表：记录 UC 与标注框。"""

    __tablename__ = "annotation"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    md5 = Column(String(64), nullable=True)
    position_id = Column(String(255), nullable=True)
    uc = Column(String(255), nullable=False)
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    label_id = Column(Integer, ForeignKey("label.id"), nullable=False)
    difficult = Column(Boolean, nullable=False, default=False)
    update_time = Column(DateTime, nullable=False, default=beijing_now, onupdate=beijing_now)
    update_id = Column(Integer, ForeignKey("user_account.id"), nullable=False)
    update_reason = Column(String(500), nullable=False)
    extra_info = Column(Text, nullable=False, default="{}")

    __table_args__ = (
        Index("idx_annotation_uc", "uc"),
        Index("idx_annotation_md5", "md5"),
        Index("idx_annotation_label_id", "label_id"),
        Index("idx_annotation_update_time", "update_time"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "md5": self.md5,
            "position_id": self.position_id,
            "uc": self.uc,
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
    uc,
    x1,
    y1,
    x2,
    y2,
    label_id,
    update_id,
    update_reason,
    md5=None,
    position_id=None,
    difficult=False,
    extra_info=None,
):
    """添加主表标注记录。"""
    session = Session()
    try:
        record = Annotation(
            md5=md5,
            position_id=position_id,
            uc=uc,
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
        logging.exception("添加标注记录失败 uc=%s label_id=%s", uc, label_id)
        return None
    finally:
        session.close()


def get_all_annotations():
    """获取全部主表标注记录。"""
    session = Session()
    try:
        records = session.query(Annotation).order_by(Annotation.id).all()
        return [record.to_dict() for record in records]
    except SQLAlchemyError:
        logging.exception("查询标注主表失败")
        return []
    finally:
        session.close()
