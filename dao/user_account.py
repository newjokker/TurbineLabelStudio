# -*- coding: utf-8 -*-
"""本地 user_account 表：人员登录信息。"""
import logging

from sqlalchemy import CheckConstraint, Column, DateTime, Index, Integer, String
from sqlalchemy.exc import SQLAlchemyError

from dao.database import Base, Session, format_beijing_time


class UserAccount(Base):
    """人员登录表。"""

    __tablename__ = "user_account"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    alias = Column(String(255), nullable=True)
    end_time = Column(DateTime, nullable=True)
    role = Column(String(50), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "role IN ('观察者', '编辑者', '管理员')",
            name="ck_user_account_role",
        ),
        Index("idx_user_account_name", "name"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "password": self.password,
            "alias": self.alias,
            "end_time": format_beijing_time(self.end_time),
            "role": self.role,
        }


def add_user_account(name, password, role, alias=None, end_time=None):
    """添加人员登录记录。"""
    if not name or not password or not role:
        logging.error("添加人员登录记录失败 name/password/role 不能为空")
        return None

    session = Session()
    try:
        record = UserAccount(
            name=name,
            password=password,
            alias=alias,
            end_time=end_time,
            role=role,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record.to_dict()
    except SQLAlchemyError:
        session.rollback()
        logging.exception("添加人员登录记录失败 name=%s", name)
        return None
    finally:
        session.close()


def get_all_user_accounts():
    """获取全部人员登录记录。"""
    session = Session()
    try:
        records = session.query(UserAccount).order_by(UserAccount.id).all()
        return [record.to_dict() for record in records]
    except SQLAlchemyError:
        logging.exception("查询人员登录表失败")
        return []
    finally:
        session.close()
