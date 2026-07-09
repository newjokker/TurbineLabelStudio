# -*- coding: utf-8 -*-

import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TURBINE_LABEL_DATA_DIR = "./logs"

LOCAL_LABEL_STUDIO_DB = os.path.join(TURBINE_LABEL_DATA_DIR, "label_studio.db")

LABEL_STUDIO_BACKUP_DIR = os.path.join(TURBINE_LABEL_DATA_DIR, "backup")

# 存放缓存文件
CACHE_DIR = os.path.join(TURBINE_LABEL_DATA_DIR, "temp")

# wav 的缓存 md5.wav
WAV_TEMP_DIR = os.path.join(CACHE_DIR, "wav")

# 图片的缓存 buc + func .jpg
IMG_TEMP_DIR = os.path.join(CACHE_DIR, "img")

