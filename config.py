# -*- coding: utf-8 -*-

import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TURBINE_LABEL_DATA_DIR = "./logs"

LOCAL_LABEL_STUDIO_DB = os.path.join(TURBINE_LABEL_DATA_DIR, "label_studio.db")

LABEL_STUDIO_BACKUP_DIR = os.path.join(TURBINE_LABEL_DATA_DIR, "backup")

# 存放临时的缓存文件
TEMP_DIR = os.path.join(TURBINE_LABEL_DATA_DIR, "temp")



