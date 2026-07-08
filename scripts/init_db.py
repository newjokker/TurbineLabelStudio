# -*- coding: utf-8 -*-
"""初始化 TurbineLabelStudio 本地数据库。"""
import os
import sys


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import LABEL_STUDIO_BACKUP_DIR, LOCAL_LABEL_STUDIO_DB
from dao.annotation import ensure_annotation_schema
from dao.database import create_all_tables

# 导入所有表模型，确保 Base.metadata 包含完整表结构和外键关系。
from dao import annotation, label, operation_log, user_account  # noqa: F401


def main():
    create_all_tables()
    rebuilt = ensure_annotation_schema()
    print(f"数据库已初始化: {LOCAL_LABEL_STUDIO_DB}")
    print(f"每日备份目录: {LABEL_STUDIO_BACKUP_DIR}")
    if rebuilt:
        print("annotation 表已按 UC/MD5 约束重建，历史标注数据已清空")


if __name__ == "__main__":
    main()
