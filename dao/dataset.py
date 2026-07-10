# -*- coding: utf-8 -*-
"""本地 dataset 表：数据集信息。"""
import logging

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.exc import SQLAlchemyError

from dao.database import Base, Session, beijing_now, format_beijing_time, json_text, json_value


class Dataset(Base):
    """数据集表：维护数据集名称和描述。"""

    __tablename__ = "dataset"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(255), nullable=False, unique=True)
    des = Column(Text, nullable=True)
    update_time = Column(DateTime, nullable=False, default=beijing_now, onupdate=beijing_now)
    extra_info = Column(Text, nullable=False, default="{}")

    __table_args__ = (
        Index("idx_dataset_name", "name"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "des": self.des,
            "update_time": format_beijing_time(self.update_time),
            "extra_info": json_value(self.extra_info),
        }


def add_dataset(name, des=None, extra_info=None):
    """添加一个数据集。"""
    if not name:
        logging.error("添加数据集失败 name 不能为空")
        return None

    session = Session()
    try:
        record = Dataset(name=name, des=des, extra_info=json_text(extra_info))
        session.add(record)
        session.commit()
        session.refresh(record)
        return record.to_dict()
    except SQLAlchemyError:
        session.rollback()
        logging.exception("添加数据集失败 name=%s", name)
        return None
    finally:
        session.close()


def get_all_datasets():
    """获取全部数据集。"""
    session = Session()
    try:
        records = session.query(Dataset).order_by(Dataset.id).all()
        return [record.to_dict() for record in records]
    except SQLAlchemyError:
        logging.exception("查询数据集失败")
        return []
    finally:
        session.close()


def get_dataset_info_by_name(name):
    """根据数据集名称查询数据集信息。"""
    if not name:
        logging.error("根据名称查询数据集失败 name 不能为空")
        return None

    session = Session()
    try:
        record = session.query(Dataset).filter_by(name=name).first()
        return record.to_dict() if record else None
    except SQLAlchemyError:
        logging.exception("根据名称查询数据集失败 name=%s", name)
        return None
    finally:
        session.close()


def delete_dataset_by_id(dataset_id):
    """根据 id 删除数据集，并同步删除 BUC/数据集关系。"""
    if dataset_id is None:
        logging.error("删除数据集失败 dataset_id 不能为空")
        return False

    session = Session()
    try:
        from dao.buc_dataset import BucDataset

        record = session.query(Dataset).filter_by(id=dataset_id).first()
        if not record:
            logging.error("删除数据集失败 dataset_id 不存在 dataset_id=%s", dataset_id)
            return False

        session.query(BucDataset).filter_by(dataset_id=dataset_id).delete(synchronize_session=False)
        session.delete(record)
        session.commit()
        return True
    except SQLAlchemyError:
        session.rollback()
        logging.exception("删除数据集失败 dataset_id=%s", dataset_id)
        return False
    finally:
        session.close()


def delete_dataset_by_name(name):
    """根据名称删除数据集，并同步删除 BUC/数据集关系。"""
    if not name:
        logging.error("删除数据集失败 name 不能为空")
        return False

    session = Session()
    try:
        from dao.buc_dataset import BucDataset

        record = session.query(Dataset).filter_by(name=name).first()
        if not record:
            logging.error("删除数据集失败 name 不存在 name=%s", name)
            return False

        session.query(BucDataset).filter_by(dataset_id=record.id).delete(synchronize_session=False)
        session.delete(record)
        session.commit()
        return True
    except SQLAlchemyError:
        session.rollback()
        logging.exception("删除数据集失败 name=%s", name)
        return False
    finally:
        session.close()
