from JoTools.utils.FileOperationUtil import FileOperationUtil
import re
from datetime import datetime, timedelta
from typing import Optional
import requests
import csv


img_dir = "/Volumes/Jokker/Code/TurbineLabelStudio/data"

url = "http://192.168.3.69:11402/blade_file/search"

csv_path = "search_result.csv"


def extract_datetime_from_filename(filename: str) -> Optional[datetime]:
    """
    从文件名中提取精确到秒的时间，返回 datetime 对象。

    支持示例：
    1. 中船海装_F01_2025_08_05_18_50_55_blade.jpg
    2. 南通启东_F02_back_2025_03_19_15_28_36.jpg
    3. 南通启东_F2_F003B1A_2026-05-25_14-41-28_南通启东_F2-#028.jpg
    """

    patterns = [
        # 格式：2025_08_05_18_50_55
        r"(?<!\d)(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})(?!\d)",

        # 格式：2026-05-25_14-41-28
        r"(?<!\d)(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})(?!\d)",
    ]

    for pattern in patterns:
        match = re.search(pattern, filename)
        if not match:
            continue

        year, month, day, hour, minute, second = map(int, match.groups())

        try:
            return datetime(year, month, day, hour, minute, second)
        except ValueError:
            return None

    return None


with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)

    writer.writerow([
        "file_name",
        "time_info",
        "info_count",
        "tags"
    ])

    for img_path in FileOperationUtil.re_all_file(img_dir, endswitch=[".jpg"]):

        file_name = FileOperationUtil.bang_path(img_path)[1]

        time_info = extract_datetime_from_filename(file_name)

        if time_info is None:
            raise ValueError(f"文件名时间格式错误: {file_name}")

        start_time = time_info - timedelta(seconds=2)
        stop_time = time_info + timedelta(seconds=2)

        data = {
            "proj_name": "WindTurbineOnline",
            "tag_and": True,
            "start_time": int(start_time.timestamp()),
            "stop_time": int(stop_time.timestamp()),
            "page": 1,
            "page_size": 10
        }

        resp = requests.post(url, json=data)
        resp.raise_for_status()

        result = resp.json()

        info_list = result.get("info", [])
        info_count = len(info_list)

        if info_count == 6:
            tags = set()

            for item in info_list:
                for tag in item.get("tags", []):
                    tags.add(tag)

            tags_str = ",".join(sorted(tags))

            print(f"{file_name}: {tags_str}")

            writer.writerow([
                file_name,
                time_info.strftime("%Y-%m-%d %H:%M:%S"),
                info_count,
                tags_str
            ])

        else:
            print(f"{file_name}: {info_count}")

            writer.writerow([
                file_name,
                time_info.strftime("%Y-%m-%d %H:%M:%S"),
                info_count,
                ""
            ])

print(f"结果已写入: {csv_path}")