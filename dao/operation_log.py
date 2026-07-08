# -*- coding: utf-8 -*-
"""本地 operation_log 表：操作日志。"""
import logging

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.exc import SQLAlchemyError

from dao.database import Base, Session, beijing_now, format_beijing_time, json_text, json_value

# 注册外键引用表到同一个 Base.metadata，避免单独导入本 DAO 时外键解析失败。
from dao import user_account  # noqa: F401


class OperationLog(Base):
    """日志表：记录单个动作对数据表的修改。"""

    __tablename__ = "operation_log"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    role_id = Column(Integer, ForeignKey("user_account.id"), nullable=False)
    act = Column(String(50), nullable=False)
    table_name = Column(String(255), nullable=False)
    update_time = Column(DateTime, nullable=False, default=beijing_now)
    change_info = Column(Text, nullable=False, default="{}")

    __table_args__ = (
        CheckConstraint(
            "act IN ('create', 'update', 'delete', 'login', 'logout', 'export', 'import')",
            name="ck_operation_log_act",
        ),
        Index("idx_operation_log_role_time", "role_id", "update_time"),
        Index("idx_operation_log_table_time", "table_name", "update_time"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "role_id": self.role_id,
            "act": self.act,
            "table_name": self.table_name,
            "update_time": format_beijing_time(self.update_time),
            "change_info": json_value(self.change_info),
        }


def add_operation_log(role_id, act, table_name, change_info=None):
    """添加一条操作日志。"""
    if not role_id or not act or not table_name:
        logging.error("添加操作日志失败 role_id/act/table_name 不能为空")
        return None

    session = Session()
    try:
        record = OperationLog(
            role_id=role_id,
            act=act,
            table_name=table_name,
            change_info=json_text(change_info),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record.to_dict()
    except SQLAlchemyError:
        session.rollback()
        logging.exception("添加操作日志失败 role_id=%s act=%s", role_id, act)
        return None
    finally:
        session.close()


def get_all_operation_logs():
    """获取全部操作日志。"""
    session = Session()
    try:
        records = session.query(OperationLog).order_by(OperationLog.id).all()
        return [record.to_dict() for record in records]
    except SQLAlchemyError:
        logging.exception("查询操作日志表失败")
        return []
    finally:
        session.close()
