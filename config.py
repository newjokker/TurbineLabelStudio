# -*- coding: utf-8 -*-

import os

if os.path.exists("/usr/data/fengji_sewrver_logs"):
    TURBINE_LABEL_DATA_DIR = "/usr/data/fengji_sewrver_logs"
else:
    TURBINE_LABEL_DATA_DIR = "/Volumes/Jokker/Code/TurbineLabelStudio/logs"

LOCAL_LABEL_STUDIO_DB = os.path.join(TURBINE_LABEL_DATA_DIR, "label_studio.db")

LABEL_STUDIO_BACKUP_DIR = os.path.join(TURBINE_LABEL_DATA_DIR, "sql_backup")

os.makedirs(LABEL_STUDIO_BACKUP_DIR, exist_ok=True)

# 存放缓存文件
CACHE_DIR = os.path.join(TURBINE_LABEL_DATA_DIR, "cache")

os.makedirs(CACHE_DIR, exist_ok=True)

# wav 的缓存 md5.wav
WAV_CACHE_DIR = os.path.join(CACHE_DIR, "wav")

# 图片的缓存 buc + func .jpg
IMG_CACHE_DIR = os.path.join(CACHE_DIR, "img")

