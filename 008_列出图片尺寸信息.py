# -*- coding: utf-8 -*-
"""列出 data/20260604 下所有图片的尺寸信息。"""

import argparse
import csv
import os
import signal
import struct
import sys
from pathlib import Path


if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

DEFAULT_IMAGE_DIR = Path("/Volumes/Jokker/Code/TurbineLabelStudio/data/20260604")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


def read_png_size(file_obj):
    file_obj.seek(16)
    width, height = struct.unpack(">II", file_obj.read(8))
    return width, height, "png"


def read_gif_size(file_obj):
    file_obj.seek(6)
    width, height = struct.unpack("<HH", file_obj.read(4))
    return width, height, "gif"


def read_bmp_size(file_obj):
    file_obj.seek(18)
    width, height = struct.unpack("<ii", file_obj.read(8))
    return width, abs(height), "bmp"


def read_webp_size(file_obj):
    file_obj.seek(0)
    header = file_obj.read(30)
    if len(header) < 30 or header[:4] != b"RIFF" or header[8:12] != b"WEBP":
        raise ValueError("不是有效的 WEBP 文件")

    chunk_type = header[12:16]
    if chunk_type == b"VP8 ":
        width, height = struct.unpack("<HH", header[26:30])
        return width & 0x3FFF, height & 0x3FFF, "webp"
    if chunk_type == b"VP8L":
        b0, b1, b2, b3 = header[21:25]
        width = 1 + (((b1 & 0x3F) << 8) | b0)
        height = 1 + (((b3 & 0x0F) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
        return width, height, "webp"
    if chunk_type == b"VP8X":
        width = 1 + int.from_bytes(header[24:27], "little")
        height = 1 + int.from_bytes(header[27:30], "little")
        return width, height, "webp"

    raise ValueError(f"不支持的 WEBP chunk: {chunk_type!r}")


def read_jpeg_size(file_obj):
    file_obj.seek(2)
    while True:
        marker_start = file_obj.read(1)
        if not marker_start:
            break
        if marker_start != b"\xff":
            continue

        marker = file_obj.read(1)
        while marker == b"\xff":
            marker = file_obj.read(1)
        if not marker:
            break

        marker_value = marker[0]
        if marker_value in {0xD8, 0xD9, 0x01} or 0xD0 <= marker_value <= 0xD7:
            continue

        segment_length_bytes = file_obj.read(2)
        if len(segment_length_bytes) != 2:
            break
        segment_length = struct.unpack(">H", segment_length_bytes)[0]
        if segment_length < 2:
            break

        if marker_value in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            data = file_obj.read(5)
            if len(data) != 5:
                break
            height, width = struct.unpack(">HH", data[1:5])
            return width, height, "jpeg"

        file_obj.seek(segment_length - 2, os.SEEK_CUR)

    raise ValueError("未找到 JPEG 尺寸信息")


def get_image_size(path):
    with path.open("rb") as file_obj:
        header = file_obj.read(12)
        if header.startswith(b"\xff\xd8"):
            return read_jpeg_size(file_obj)
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return read_png_size(file_obj)
        if header[:6] in {b"GIF87a", b"GIF89a"}:
            return read_gif_size(file_obj)
        if header.startswith(b"BM"):
            return read_bmp_size(file_obj)
        if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
            return read_webp_size(file_obj)

    raise ValueError("不支持或无法识别的图片格式")


def iter_image_files(image_dir):
    for path in sorted(image_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            yield path


def main():
    parser = argparse.ArgumentParser(description="列出图片尺寸信息")
    parser.add_argument("--dir", default=str(DEFAULT_IMAGE_DIR), help="图片目录")
    parser.add_argument("--output", help="输出 CSV 文件路径；不传则打印到终端")
    args = parser.parse_args()

    image_dir = Path(args.dir)
    rows = []
    for path in iter_image_files(image_dir):
        try:
            width, height, image_format = get_image_size(path)
            error = ""
        except Exception as exc:
            width, height, image_format = "", "", ""
            error = str(exc)

        rows.append(
            {
                "path": str(path),
                "filename": path.name,
                "format": image_format,
                "width": width,
                "height": height,
                "size_bytes": path.stat().st_size,
                "error": error,
            }
        )

    output_file = open(args.output, "w", newline="", encoding="utf-8-sig") if args.output else sys.stdout
    broken_pipe = False
    try:
        writer = csv.DictWriter(
            output_file,
            fieldnames=["path", "filename", "format", "width", "height", "size_bytes", "error"],
        )
        writer.writeheader()
        writer.writerows(rows)
    except BrokenPipeError:
        broken_pipe = True
    finally:
        if args.output:
            output_file.close()

    if not broken_pipe:
        print(f"共扫描图片 {len(rows)} 张", file=sys.stderr)


if __name__ == "__main__":
    main()
