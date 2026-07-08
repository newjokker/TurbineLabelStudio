# -*- coding: utf-8 -*-
"""本地 uc_md5_map 表：UC 与 MD5、测点位置映射关系。"""
import logging

from sqlalchemy import CheckConstraint, Column, Index, String
from sqlalchemy.exc import SQLAlchemyError

from dao.database import Base, Session


class UcMd5Map(Base):
    """UC md5 映射关系表。"""

    __tablename__ = "uc_md5_map"

    md5 = Column(String(32), primary_key=True, nullable=False)
    position_id = Column(String(255), nullable=True)            # B1A, 叶片1 测点 A 
    uc = Column(String(7), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "length(uc) = 7 AND substr(uc, 1, 1) GLOB '[A-Z]' AND uc NOT GLOB '*[^A-Za-z0-9]*'",
            name="ck_uc_md5_map_uc_format",
        ),
        CheckConstraint(
            "length(md5) = 32 AND md5 NOT GLOB '*[^0-9a-f]*'",
            name="ck_uc_md5_map_md5_format",
        ),
        Index("idx_uc_md5_map_uc", "uc"),
        Index("idx_uc_md5_map_position_id", "position_id"),
    )

    def to_dict(self):
        return {
            "md5": self.md5,
            "position_id": self.position_id,
            "uc": self.uc,
        }


def add_uc_md5_map(md5, uc, position_id=None):
    """添加一条 UC 与 MD5 映射记录。"""
    if not md5 or not uc:
        logging.error("添加 UC/MD5 映射失败 md5 和 uc 不能为空")
        return None

    session = Session()
    try:
        record = UcMd5Map(md5=md5, position_id=position_id, uc=uc)
        session.add(record)
        session.commit()
        session.refresh(record)
        return record.to_dict()
    except SQLAlchemyError:
        session.rollback()
        logging.exception("添加 UC/MD5 映射失败 md5=%s uc=%s", md5, uc)
        return None
    finally:
        session.close()


def get_all_uc_md5_maps():
    """获取全部 UC 与 MD5 映射记录。"""
    session = Session()
    try:
        records = session.query(UcMd5Map).order_by(UcMd5Map.md5).all()
        return [record.to_dict() for record in records]
    except SQLAlchemyError:
        logging.exception("查询 UC/MD5 映射表失败")
        return []
    finally:
        session.close()


def get_uc_md5_maps_by_uc(uc):
    """根据 UC 获取映射记录。"""
    session = Session()
    try:
        records = session.query(UcMd5Map).filter_by(uc=uc).order_by(UcMd5Map.md5).all()
        return [record.to_dict() for record in records]
    except SQLAlchemyError:
        logging.exception("根据 UC 查询 UC/MD5 映射失败 uc=%s", uc)
        return []
    finally:
        session.close()


def get_uc_md5_maps_by_md5(md5):
    """根据 MD5 获取映射记录。"""
    session = Session()
    try:
        record = session.query(UcMd5Map).filter_by(md5=md5).first()
        return record.to_dict() if record else None
    except SQLAlchemyError:
        logging.exception("根据 MD5 查询 UC/MD5 映射失败 md5=%s", md5)
        return None
    finally:
        session.close()


def get_uc_by_md5(md5):
    """根据 MD5 获取 UC。"""
    session = Session()
    try:
        record = session.query(UcMd5Map.uc).filter_by(md5=md5).first()
        return record.uc if record else None
    except SQLAlchemyError:
        logging.exception("根据 MD5 查询 UC 失败 md5=%s", md5)
        return None
    finally:
        session.close()


def get_md5_list_by_uc(uc):
    """根据 UC 获取 MD5 列表。"""
    session = Session()
    try:
        records = session.query(UcMd5Map.md5).filter_by(uc=uc).order_by(UcMd5Map.md5).all()
        return [record.md5 for record in records]
    except SQLAlchemyError:
        logging.exception("根据 UC 查询 MD5 列表失败 uc=%s", uc)
        return []
    finally:
        session.close()
