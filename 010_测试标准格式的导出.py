

import os

from scripts.format_transform import save_img_and_xml
from dao.wav_buc import get_all_buc_list


FUNC_NAME = "wh_jzp_before_20260708"
SAVE_DIR = "/Volumes/Jokker/Code/TurbineLabelStudio/data/save_res"


def export_all_buc(func_name=FUNC_NAME, save_dir=SAVE_DIR):
    """批量导出所有 BUC 的标准格式数据。"""
    os.makedirs(save_dir, exist_ok=True)

    buc_list = get_all_buc_list()
    total = len(buc_list)
    success_count = 0
    skip_count = 0
    fail_items = []

    for index, buc in enumerate(buc_list, start=1):
        try:
            result = save_img_and_xml(buc, func_name, save_dir)
            success_count += 1
            print(
                f"[{index}/{total}] 导出成功: {buc} "
                f"标注数={result['annotation_count']} 目录={result['save_dir']}"
            )
        except Exception as exc:
            fail_items.append((buc, str(exc)))
            print(f"[{index}/{total}] 导出失败: {buc} 原因={exc}")

    print(
        "导出完成 "
        f"总数={total} 成功={success_count} 跳过={skip_count} 失败={len(fail_items)} "
        f"保存目录={save_dir}"
    )

    if fail_items:
        print("失败列表:")
        for buc, reason in fail_items:
            print(f"  {buc}: {reason}")

    return {
        "total": total,
        "success": success_count,
        "skip": skip_count,
        "fail": len(fail_items),
        "fail_items": fail_items,
        "save_dir": save_dir,
    }


if __name__ == "__main__":
    export_all_buc()
