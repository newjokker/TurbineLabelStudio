# -*- coding: utf-8 -*-
"""初始化 TurbineLabelStudio 本地数据库。"""
import os
import sys


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import LABEL_STUDIO_BACKUP_DIR, LOCAL_LABEL_STUDIO_DB
from dao.database import create_all_tables

# 导入所有表模型，确保 Base.metadata 包含完整表结构和外键关系。
from dao import annotation, annotation_lock, buc_dataset, dataset, label, operation_log, user_account, user_permission, wav_buc  # noqa: F401


def main():
    create_all_tables()
    print(f"数据库已初始化: {LOCAL_LABEL_STUDIO_DB}")
    print(f"手动备份目录: {LABEL_STUDIO_BACKUP_DIR}")


if __name__ == "__main__":
    main()
