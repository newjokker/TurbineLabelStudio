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


def get_bucs_by_dataset_id(dataset_id):
    """根据数据集 id 查询包含的 BUC 列表。"""
    session = Session()
    try:
        records = session.query(BucDataset.buc).filter_by(dataset_id=dataset_id).order_by(BucDataset.buc).all()
        return [record.buc for record in records]
    except SQLAlchemyError:
        logging.exception("根据数据集 id 查询 BUC 列表失败 dataset_id=%s", dataset_id)
        return []
    finally:
        session.close()


def get_bucs_by_dataset_name(name):
    """根据数据集名称查询包含的 BUC 列表。"""
    if not name:
        logging.error("根据数据集名称查询 BUC 列表失败 name 不能为空")
        return []

    session = Session()
    try:
        records = (
            session.query(BucDataset.buc)
            .join(Dataset, Dataset.id == BucDataset.dataset_id)
            .filter(Dataset.name == name)
            .order_by(BucDataset.buc)
            .all()
        )
        return [record.buc for record in records]
    except SQLAlchemyError:
        logging.exception("根据数据集名称查询 BUC 列表失败 name=%s", name)
        return []
    finally:
        session.close()


def get_bucs_not_assign_dataset(exclude_dataset_list=None):
    """找到哪些 buc 是没有被指定数据集的，被 exclude_dataset_list 数据集列表中的数据集指定不算被指定"""
    session = Session()
    try:
        exclude_dataset_ids = _normalize_dataset_ids(session, exclude_dataset_list)
        all_buc_records = session.query(WavBuc.buc).distinct().order_by(WavBuc.buc).all()
        assigned_query = session.query(BucDataset.buc).distinct()
        if exclude_dataset_ids:
            assigned_query = assigned_query.filter(~BucDataset.dataset_id.in_(exclude_dataset_ids))
        assigned_bucs = {record.buc for record in assigned_query.all()}
        return [record.buc for record in all_buc_records if record.buc not in assigned_bucs]
    except SQLAlchemyError:
        logging.exception("查询未分配数据集的 BUC 失败 exclude_dataset_list=%s", exclude_dataset_list)
        return []
    finally:
        session.close()


def _normalize_dataset_ids(session, dataset_list):
    """把数据集 id/name/dict 列表归一成数据集 id 集合。"""
    if not dataset_list:
        return set()

    if isinstance(dataset_list, (str, int)):
        dataset_list = [dataset_list]

    dataset_ids = set()
    dataset_names = set()
    for item in dataset_list:
        if isinstance(item, dict):
            if item.get("id") is not None:
                dataset_ids.add(int(item["id"]))
            elif item.get("name"):
                dataset_names.add(str(item["name"]))
            continue
        if isinstance(item, int) or (isinstance(item, str) and item.isdigit()):
            dataset_ids.add(int(item))
        elif item:
            dataset_names.add(str(item))

    if dataset_names:
        records = session.query(Dataset.id).filter(Dataset.name.in_(dataset_names)).all()
        dataset_ids.update(record.id for record in records)
    return dataset_ids
