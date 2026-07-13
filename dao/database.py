# -*- coding: utf-8 -*-
"""TurbineLabelStudio SQLite 公共连接配置。"""
import json
import logging
import os
import re
import sqlite3
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from config import LABEL_STUDIO_BACKUP_DIR, LOCAL_LABEL_STUDIO_DB


DATABASE_URL = f"sqlite:///{LOCAL_LABEL_STUDIO_DB}"

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
BACKUP_FILENAME_RE = re.compile(
    r"^label_studio_\d{8}(?:_\d{6}(?:_\d{6})?)?\.db$"
)


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
    # drop_incompatible_annotation_table()
    Base.metadata.create_all(engine)


def drop_incompatible_annotation_table():
    """annotation 表结构不匹配当前模型时直接删除，随后由 create_all 重建。"""
    if not inspect(engine).has_table("annotation"):
        return False

    columns = {column["name"] for column in inspect(engine).get_columns("annotation")}
    required_columns = {
        "id",
        "buc",
        "func",
        "x1",
        "y1",
        "x2",
        "y2",
        "label_id",
        "difficult",
        "update_time",
        "update_id",
        "update_reason",
        "extra_info",
    }
    if required_columns.issubset(columns) and "uc" not in columns:
        return False

    Base.metadata.tables["annotation"].drop(engine, checkfirst=True)
    logging.warning("annotation 表结构不兼容，已删除并将按当前模型重建")
    return True


def _backup_sqlite_database(source_path, backup_path):
    """使用 SQLite 在线备份 API 创建包含 WAL 最新数据的一致快照。"""
    backup_dir = os.path.dirname(backup_path)
    os.makedirs(backup_dir, exist_ok=True)

    temp_fd, temp_path = tempfile.mkstemp(
        prefix=f".{os.path.basename(backup_path)}.",
        suffix=".tmp",
        dir=backup_dir,
    )
    os.close(temp_fd)

    source_conn = None
    backup_conn = None
    try:
        source_conn = sqlite3.connect(source_path, timeout=30)
        backup_conn = sqlite3.connect(temp_path, timeout=30)
        source_conn.backup(backup_conn)
        backup_conn.commit()

        integrity_result = backup_conn.execute("PRAGMA integrity_check").fetchone()
        if not integrity_result or integrity_result[0] != "ok":
            raise sqlite3.DatabaseError(f"备份完整性检查失败: {integrity_result}")

        backup_conn.close()
        backup_conn = None
        source_conn.close()
        source_conn = None
        os.replace(temp_path, backup_path)
        return backup_path
    finally:
        if backup_conn is not None:
            backup_conn.close()
        if source_conn is not None:
            source_conn.close()
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _backup_file_info(backup_path):
    stat = os.stat(backup_path)
    return {
        "name": os.path.basename(backup_path),
        "size_bytes": stat.st_size,
        "created_time": datetime.fromtimestamp(stat.st_mtime, BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S"),
    }


def create_database_backup():
    """由用户主动创建一个带精确时间的 SQLite 一致性快照。"""
    if not os.path.isfile(LOCAL_LABEL_STUDIO_DB):
        raise FileNotFoundError(f"数据库文件不存在: {LOCAL_LABEL_STUDIO_DB}")

    now_text = datetime.now(BEIJING_TZ).strftime("%Y%m%d_%H%M%S_%f")
    backup_path = os.path.join(LABEL_STUDIO_BACKUP_DIR, f"label_studio_{now_text}.db")
    _backup_sqlite_database(LOCAL_LABEL_STUDIO_DB, backup_path)
    return _backup_file_info(backup_path)


def list_database_backups():
    """列出备份目录中由本项目创建的数据库备份。"""
    os.makedirs(LABEL_STUDIO_BACKUP_DIR, exist_ok=True)
    items = []
    for file_name in os.listdir(LABEL_STUDIO_BACKUP_DIR):
        if not BACKUP_FILENAME_RE.fullmatch(file_name):
            continue
        backup_path = os.path.join(LABEL_STUDIO_BACKUP_DIR, file_name)
        if os.path.isfile(backup_path):
            items.append(_backup_file_info(backup_path))
    return sorted(items, key=lambda item: (item["created_time"], item["name"]), reverse=True)


def get_database_backup_path(file_name):
    """校验备份文件名并返回已存在的备份路径。"""
    if not isinstance(file_name, str) or not BACKUP_FILENAME_RE.fullmatch(file_name):
        return None
    backup_path = os.path.join(LABEL_STUDIO_BACKUP_DIR, file_name)
    return backup_path if os.path.isfile(backup_path) else None


def delete_database_backup(file_name):
    """删除指定历史备份，成功返回被删除的备份信息。"""
    backup_path = get_database_backup_path(file_name)
    if not backup_path:
        return None
    item = _backup_file_info(backup_path)
    os.remove(backup_path)
    return item
