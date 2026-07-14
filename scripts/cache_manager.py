# -*- coding: utf-8 -*-
"""WAV 和图片缓存管理工具。"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path
import requests
from config import IMG_CACHE_DIR, WAV_CACHE_DIR  
from dao.wav_buc import get_format_wave_md5_info_by_buc  
from scripts.buc_func_util import get_buc_image_by_func, get_wav_image_duration_seconds


WAV_SUFFIX = ".wav"
IMG_SUFFIX = ".jpg"
MD5_RE = re.compile(r"^[0-9a-fA-F]{32}$")


def _ensure_cache_dirs():
    """确保缓存目录存在。"""
    os.makedirs(WAV_CACHE_DIR, exist_ok=True)
    os.makedirs(IMG_CACHE_DIR, exist_ok=True)


def _normalize_md5(md5):
    """校验并统一 md5 字符串格式。"""
    if not md5 or not MD5_RE.match(md5):
        raise ValueError(f"md5 格式不正确: {md5}")
    return md5.lower()


def load_wav_by_md5(md5, save_dir):
    """根据 md5 从远端下载 wav 到 save_dir。"""
    md5 = _normalize_md5(md5)
    os.makedirs(save_dir, exist_ok=True)

    url = "http://192.168.3.69:11402/file/download/" + md5 + WAV_SUFFIX
    resp = requests.get(url, timeout=60)
    if resp.status_code == 200:
        with open(os.path.join(save_dir, f"{md5}.wav"), "wb") as f:
            f.write(resp.content)
        return True
    return False


def _get_img_cache_path(buc, func_name):
    """获取 buc + func_name 对应的图片缓存路径。"""
    if not buc or not func_name:
        raise ValueError("buc 和 func_name 不能为空")
    return os.path.join(IMG_CACHE_DIR, func_name, f"{buc}_{func_name}{IMG_SUFFIX}")


def get_ordered_wave_md5_list_by_buc(buc):
    """根据 BUC 获取按 B1A/B1B/B2A/B2B/B3A/B3B 排序的 6 个 wav md5。"""
    md5_list = get_format_wave_md5_info_by_buc(buc=buc)
    if md5_list:
        return md5_list

    logging.error("根据 BUC 获取 6 个 WAV MD5 失败 buc=%s", buc)
    return None


def get_img_path_by_buc_func(buc, func_name):
    """返回 buc + func_name 对应的图片路径；缓存不存在则生成。"""
    _ensure_cache_dirs()

    img_path = _get_img_cache_path(buc, func_name)
    if os.path.isfile(img_path):
        return img_path

    md5_list = get_ordered_wave_md5_list_by_buc(buc)
    if not md5_list:
        return None

    wav_files = []
    for md5 in md5_list:
        wav_path = get_wav_path_by_md5(md5)
        if not wav_path:
            return None
        wav_files.append(wav_path)

    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    res = get_buc_image_by_func(wav_files, func_name=func_name, save_path=img_path)
    if res and os.path.isfile(img_path):
        return img_path

    logging.error("生成图片缓存失败 buc=%s func_name=%s img_path=%s", buc, func_name, img_path)
    return None


def get_img_duration_by_buc(buc):
    """返回 BUC mel 图片横轴实际使用的秒数。"""
    md5_list = get_ordered_wave_md5_list_by_buc(buc)
    if not md5_list:
        return None

    wav_files = []
    for md5 in md5_list:
        wav_path = get_wav_path_by_md5(md5)
        if not wav_path:
            return None
        wav_files.append(wav_path)

    try:
        return get_wav_image_duration_seconds(wav_files)
    except (OSError, RuntimeError, ValueError):
        logging.exception("获取 mel 图片时长失败 buc=%s", buc)
        return None


def get_wav_path_by_md5(md5):
    """从 WAV_CACHE_DIR 获取 md5.wav；不存在则下载，成功返回路径，失败返回 None。"""
    md5 = _normalize_md5(md5)
    _ensure_cache_dirs()

    wav_path = os.path.join(WAV_CACHE_DIR, f"{md5}.wav")
    if os.path.isfile(wav_path):
        return wav_path

    if load_wav_by_md5(md5, WAV_CACHE_DIR) and os.path.isfile(wav_path):
        return wav_path

    logging.error("获取 WAV 缓存失败 md5=%s", md5)
    return None
