
import os
import shutil
from dao.annotation import get_ana_by_buc_func
from scripts.cache_manager import get_img_path_by_buc_func
from JoTools.txkjRes.deteRes import DeteRes


def _remove_appledouble_files(target_dir):
    """清理 macOS 在外置盘上可能产生的 ._* 元数据文件。"""
    for file_name in os.listdir(target_dir):
        if file_name.startswith("._"):
            os.remove(os.path.join(target_dir, file_name))


# 将数据库中的标注修改为 xml 格式，直接调用 JoTools 模块即可
def save_img_and_xml(buc, func, save_dir):
    """导出单个 BUC 的标准格式数据。

    标准格式：
        save_dir/
            BUC_000001_func.jpg
            BUC_000001_func.xml

    Returns:
        成功返回导出结果字典。
    """
    os.makedirs(save_dir, exist_ok=True)

    img_path = get_img_path_by_buc_func(buc=buc, func_name=func)
    if img_path is None:
        raise ValueError( f"未找到图片路径:{buc}, {func}")

    ana_info = get_ana_by_buc_func(buc=buc, func_name=func)
    if ana_info is None:
        ana_info = []

    xml_save_path = os.path.join(save_dir, f"{buc}_{func}.xml")
    img_save_path = os.path.join(save_dir, f"{buc}_{func}.jpg")

    shutil.copyfile(img_path, img_save_path)

    dete_res = DeteRes(assign_img_path=img_save_path)
    for obj in ana_info:
        dete_res.add_obj(
            x1=obj["x1"],
            y1=obj["y1"],
            x2=obj["x2"],
            y2=obj["y2"],
            tag=obj["label"],
        )

    dete_res.save_to_xml(xml_save_path)
    _remove_appledouble_files(save_dir)

    return {
        "buc": buc,
        "func": func,
        "save_dir": save_dir,
        "img_path": img_save_path,
        "xml_path": xml_save_path,
        "annotation_count": len(ana_info),
    }


