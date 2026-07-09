# -*- coding: utf-8 -*-
"""本地 label 表：标签信息。"""
import colorsys
import logging
import random

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.exc import SQLAlchemyError

from dao.database import Base, Session, beijing_now, format_beijing_time, json_text, json_value


def random_label_color():
    """生成适合声谱图背景的标签色：避开红色和过暗颜色。"""
    hue = random.choice((
        random.uniform(25, 75),
        random.uniform(90, 175),
        random.uniform(195, 315),
    )) / 360
    saturation = random.uniform(0.68, 0.9)
    lightness = random.uniform(0.52, 0.68)
    red, green, blue = colorsys.hls_to_rgb(hue, lightness, saturation)
    return f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}"


def ensure_label_color(extra_info):
    """如果 extra_info 没有指定颜色，就补一个安全随机色。"""
    extra = json_value(extra_info)
    if not isinstance(extra, dict):
        extra = {}
    if not extra.get("color"):
        extra["color"] = random_label_color()
    return extra


class Label(Base):
    """标签表：维护标签名称、描述和标注方法。"""

    __tablename__ = "label"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    label = Column(String(255), nullable=False, unique=True)
    update_time = Column(DateTime, nullable=False, default=beijing_now, onupdate=beijing_now)
    des = Column(Text, nullable=True)
    update_by = Column(String(255), nullable=True)
    extra_info = Column(Text, nullable=False, default="{}")

    __table_args__ = (
        Index("idx_label_label", "label"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "update_time": format_beijing_time(self.update_time),
            "des": self.des,
            "update_by": self.update_by,
            "extra_info": json_value(self.extra_info),
        }


def add_label(label, des=None, update_by=None, extra_info=None):
    """添加标签记录。"""
    if not label:
        logging.error("添加标签失败 label 不能为空")
        return None

    session = Session()
    try:
        record = Label(
            label=label,
            des=des,
            update_by=update_by,
            extra_info=json_text(ensure_label_color(extra_info)),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record.to_dict()
    except SQLAlchemyError:
        session.rollback()
        logging.exception("添加标签失败 label=%s", label)
        return None
    finally:
        session.close()


def get_all_labels():
    """获取全部标签。"""
    session = Session()
    try:
        records = session.query(Label).order_by(Label.id).all()
        return [record.to_dict() for record in records]
    except SQLAlchemyError:
        logging.exception("查询标签表失败")
        return []
    finally:
        session.close()


def get_label_info_by_label(label):
    """根据输入的 label 字符串返回对应的 label 信息"""
    if not label:
        logging.error("根据 label 查询标签失败 label 不能为空")
        return None

    session = Session()
    try:
        record = session.query(Label).filter_by(label=label).first()
        return record.to_dict() if record else None
    except SQLAlchemyError:
        logging.exception("根据 label 查询标签失败 label=%s", label)
        return None
    finally:
        session.close()


def get_label_info_by_id(label_id):
    """根据 label 的 id 返回对应的 label 信息"""
    if label_id is None:
        logging.error("根据 id 查询标签失败 label_id 不能为空")
        return None

    session = Session()
    try:
        record = session.query(Label).filter_by(id=label_id).first()
        return record.to_dict() if record else None
    except SQLAlchemyError:
        logging.exception("根据 id 查询标签失败 label_id=%s", label_id)
        return None
    finally:
        session.close()
