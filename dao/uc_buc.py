# -*- coding: utf-8 -*-
"""本地 uc_buc 表：UC 与 BUC、生成方法映射关系。"""
import logging

from sqlalchemy import CheckConstraint, Column, Index, String
from sqlalchemy.exc import SQLAlchemyError

from dao.database import Base, Session

# 注册外键引用表到同一个 Base.metadata，避免单独导入本 DAO 时外键解析失败。
from dao.wav_buc import WavBuc


class UcBuc(Base):
    """UC 与 BUC、生成方法映射表。"""

    __tablename__ = "uc_buc"

    uc = Column(String(7), primary_key=True, nullable=False)
    buc = Column(String(255), nullable=False)
    func = Column(String(255), nullable=False)                  # 使用 buc 对应的 .wav 文件生成 uc 对应的 image 图的方法

    __table_args__ = (
        CheckConstraint(
            "length(uc) = 7 AND substr(uc, 1, 1) GLOB '[A-Z]' AND uc NOT GLOB '*[^A-Za-z0-9]*'",
            name="ck_uc_buc_uc_format",
        ),
        CheckConstraint(
            "length(func) > 0",
            name="ck_uc_buc_func_not_empty",
        ),
        CheckConstraint(
            "length(buc) = 10 AND buc GLOB 'BUC_[0-9][0-9][0-9][0-9][0-9][0-9]'",
            name="ck_uc_buc_buc_format",
        ),
        Index("idx_uc_buc_buc", "buc"),
        Index("idx_uc_buc_func", "func"),
    )

    def to_dict(self):
        return {
            "uc": self.uc,
            "buc": self.buc,
            "func": self.func,
        }


def add_uc_buc(uc, buc, func):
    """添加一条 UC 与 BUC、方法映射记录。"""
    if not uc or not buc or not func:
        logging.error("添加 UC/BUC 映射失败 uc、buc、func 不能为空")
        return None

    session = Session()
    try:
        buc_exists = session.query(WavBuc.wave_md5).filter_by(buc=buc).first()
        if not buc_exists:
            logging.error("添加 UC/BUC 映射失败 buc 不存在 buc=%s", buc)
            return None

        record = UcBuc(uc=uc, buc=buc, func=func)
        session.add(record)
        session.commit()
        session.refresh(record)
        return record.to_dict()
    except SQLAlchemyError:
        session.rollback()
        logging.exception("添加 UC/BUC 映射失败 uc=%s buc=%s func=%s", uc, buc, func)
        return None
    finally:
        session.close()


def get_all_uc_buc():
    """获取全部 UC 与 BUC、方法映射记录。"""
    session = Session()
    try:
        records = session.query(UcBuc).order_by(UcBuc.uc).all()
        return [record.to_dict() for record in records]
    except SQLAlchemyError:
        logging.exception("查询 uc_buc 表失败")
        return []
    finally:
        session.close()


def get_uc_buc_by_uc(uc):
    """根据 UC 获取映射记录。"""
    session = Session()
    try:
        record = session.query(UcBuc).filter_by(uc=uc).first()
        return record.to_dict() if record else None
    except SQLAlchemyError:
        logging.exception("根据 UC 查询 UC/BUC 映射失败 uc=%s", uc)
        return None
    finally:
        session.close()


def get_uc_list_by_buc(buc):
    """根据 BUC 获取 UC 列表。"""
    session = Session()
    try:
        records = session.query(UcBuc.uc).filter_by(buc=buc).order_by(UcBuc.uc).all()
        return [record.uc for record in records]
    except SQLAlchemyError:
        logging.exception("根据 BUC 查询 UC 列表失败 buc=%s", buc)
        return []
    finally:
        session.close()
