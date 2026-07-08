# -*- coding: utf-8 -*-
"""TurbineLabelStudio SQLite 公共连接配置。"""
import json
import logging
import os
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from config import LABEL_STUDIO_BACKUP_DIR, LOCAL_LABEL_STUDIO_DB


DATABASE_URL = f"sqlite:///{LOCAL_LABEL_STUDIO_DB}"

os.makedirs(os.path.dirname(LOCAL_LABEL_STUDIO_DB), exist_ok=True)
os.makedirs(LABEL_STUDIO_BACKUP_DIR, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "timeout": 30,
        "check_same_thread": False,
    },
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """每次数据库连接建立时设置 SQLite PRAGMA。"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA wal_autocheckpoint=1000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


Base = declarative_base()
Session = sessionmaker(bind=engine)
BEIJING_TZ = ZoneInfo("Asia/Shanghai")


def beijing_now():
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)


def format_beijing_time(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.strftime("%Y-%m-%d %H:%M:%S")


def json_text(value):
    if value is None:
        return "{}"
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def json_value(value):
    if not value:
        return {}
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return value


def create_all_tables():
    """创建所有已经导入到 Base.metadata 的表。"""
    Base.metadata.create_all(engine)
    backup_database_once_per_day()


def backup_database_once_per_day():
    """每天保留一份 SQLite 文件备份。"""
    if not os.path.exists(LOCAL_LABEL_STUDIO_DB):
        return None

    today = datetime.now(BEIJING_TZ).strftime("%Y%m%d")
    backup_path = os.path.join(LABEL_STUDIO_BACKUP_DIR, f"label_studio_{today}.db")
    if os.path.exists(backup_path):
        return backup_path

    try:
        shutil.copy2(LOCAL_LABEL_STUDIO_DB, backup_path)
        return backup_path
    except OSError:
        logging.exception("备份 label_studio 数据库失败 path=%s", backup_path)
        return None
