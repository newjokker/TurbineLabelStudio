# -*- coding: utf-8 -*-
"""本地 buc_dataset 表：BUC 与数据集的多对多关系。"""
import logging

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Integer, String
from sqlalchemy.exc import SQLAlchemyError

from dao.database import Base, Session
from dao.dataset import Dataset
from dao.wav_buc import WavBuc


class BucDataset(Base):
    """BUC 与数据集关系表。"""

    __tablename__ = "buc_dataset"

    dataset_id = Column(Integer, ForeignKey("dataset.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    buc = Column(String(10), primary_key=True, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "length(buc) = 10 AND buc GLOB 'BUC_[0-9][0-9][0-9][0-9][0-9][0-9]'",
            name="ck_buc_dataset_buc_format",
        ),
        Index("idx_buc_dataset_buc", "buc"),
        Index("idx_buc_dataset_dataset_id", "dataset_id"),
    )

    def to_dict(self):
        return {
            "dataset_id": self.dataset_id,
            "buc": self.buc,
        }


def add_buc_dataset(dataset_id, buc):
    """把一个 BUC 加入指定数据集。"""
    if dataset_id is None or not buc:
        logging.error("添加 BUC/数据集关系失败 dataset_id/buc 不能为空")
        return None

    session = Session()
    try:
        if not session.query(Dataset.id).filter_by(id=dataset_id).first():
            logging.error("添加 BUC/数据集关系失败 dataset_id 不存在 dataset_id=%s", dataset_id)
            return None
        if not session.query(WavBuc.buc).filter_by(buc=buc).first():
            logging.error("添加 BUC/数据集关系失败 buc 不存在 buc=%s", buc)
            return None

        record = session.query(BucDataset).filter_by(dataset_id=dataset_id, buc=buc).first()
        if record:
            return record.to_dict()

        record = BucDataset(dataset_id=dataset_id, buc=buc)
        session.add(record)
        session.commit()
        return record.to_dict()
    except SQLAlchemyError:
        session.rollback()
        logging.exception("添加 BUC/数据集关系失败 dataset_id=%s buc=%s", dataset_id, buc)
        return None
    finally:
        session.close()


def get_dataset_ids_by_buc(buc):
    """查询某个 BUC 所属的数据集 id 列表。"""
    session = Session()
    try:
        records = session.query(BucDataset.dataset_id).filter_by(buc=buc).order_by(BucDataset.dataset_id).all()
        return [record.dataset_id for record in records]
    except SQLAlchemyError:
        logging.exception("查询 BUC 所属数据集失败 buc=%s", buc)
        return []
    finally:
        session.close()


def get_bucs_by_dataset(dataset_id):
    """查询某个数据集包含的 BUC 列表。"""
    session = Session()
    try:
        records = session.query(BucDataset.buc).filter_by(dataset_id=dataset_id).order_by(BucDataset.buc).all()
        return [record.buc for record in records]
    except SQLAlchemyError:
        logging.exception("查询数据集 BUC 列表失败 dataset_id=%s", dataset_id)
        return []
    finally:
        session.close()
