# -*- coding: utf-8 -*-
"""本地 wav_buc 表：WAV MD5 与 BUC 映射关系。"""
import logging

from sqlalchemy import CheckConstraint, Column, Index, String, cast, func
from sqlalchemy import Integer as SqlInteger
from sqlalchemy.exc import SQLAlchemyError
from dao.database import Base, Session


class WavBuc(Base):
    """WAV MD5 与 BUC 映射表。"""

    __tablename__ = "wav_buc"

    wave_md5 = Column(String(32), primary_key=True, nullable=False)
    position_id = Column(String(255), nullable=False)
    buc = Column(String(255), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "length(wave_md5) = 32 AND wave_md5 NOT GLOB '*[^0-9a-f]*'",
            name="ck_wav_buc_wave_md5_format",
        ),
        CheckConstraint(
            "length(position_id) > 0",
            name="ck_wav_buc_position_id_not_empty",
        ),
        CheckConstraint(
            "length(buc) = 10 AND buc GLOB 'BUC_[0-9][0-9][0-9][0-9][0-9][0-9]'",
            name="ck_wav_buc_buc_format",
        ),
        Index("idx_wav_buc_position_id", "position_id"),
        Index("idx_wav_buc_buc", "buc"),
    )

    def to_dict(self):
        return {
            "wave_md5": self.wave_md5,
            "position_id": self.position_id,
            "buc": self.buc,
        }


def generate_next_buc(session):
    """生成下一个 BUC 编码：BUC_000001、BUC_000002..."""
    max_number = (
        session.query(func.max(cast(func.substr(WavBuc.buc, 5), SqlInteger)))
        .filter(WavBuc.buc.like("BUC_%"))
        .scalar()
    ) or 0
    return f"BUC_{max_number + 1:06d}"


def add_wav_buc(wave_position_id):
    """添加一组 WAV MD5 与 BUC 映射记录。

    Args:
        wave_position_id: {wave_md5: position_id}

    Returns:
        {"buc": "BUC_000001", "items": [...]}，失败返回 None。
    """
    if not isinstance(wave_position_id, dict) or not wave_position_id:
        logging.error("添加 WAV/BUC 映射失败 wave_position_id 必须是非空字典")
        return None

    for wave_md5, position_id in wave_position_id.items():
        if not wave_md5 or not position_id:
            logging.error("添加 WAV/BUC 映射失败 wave_md5 和 position_id 不能为空")
            return None

    session = Session()
    try:
        existing = (
            session.query(WavBuc.wave_md5)
            .filter(WavBuc.wave_md5.in_(list(wave_position_id.keys())))
            .all()
        )
        if existing:
            logging.error(
                "添加 WAV/BUC 映射失败 wave_md5 已存在 existing=%s",
                [row.wave_md5 for row in existing],
            )
            return None

        buc = generate_next_buc(session)
        records = [
            WavBuc(wave_md5=wave_md5, position_id=position_id, buc=buc)
            for wave_md5, position_id in wave_position_id.items()
        ]
        session.add_all(records)
        session.commit()
        for record in records:
            session.refresh(record)
        return {
            "buc": buc,
            "items": [record.to_dict() for record in records],
        }
    except SQLAlchemyError:
        session.rollback()
        logging.exception("添加 WAV/BUC 映射失败 wave_position_id=%s", wave_position_id)
        return None
    finally:
        session.close()


def get_buc_by_wave_md5(wave_md5):
    """根据 WAV MD5 获取 BUC。"""
    session = Session()
    try:
        record = session.query(WavBuc.buc).filter_by(wave_md5=wave_md5).first()
        return record.buc if record else None
    except SQLAlchemyError:
        logging.exception("根据 WAV MD5 查询 BUC 失败 wave_md5=%s", wave_md5)
        return None
    finally:
        session.close()


def get_wave_md5_list_by_buc(buc):
    """根据 BUC 获取 WAV MD5 列表。"""
    session = Session()
    try:
        records = session.query(WavBuc.wave_md5).filter_by(buc=buc).order_by(WavBuc.wave_md5).all()
        return [record.wave_md5 for record in records]
    except SQLAlchemyError:
        logging.exception("根据 BUC 查询 WAV MD5 列表失败 buc=%s", buc)
        return []
    finally:
        session.close()
