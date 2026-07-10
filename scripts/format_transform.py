
import os
import shutil
import xml.etree.ElementTree as ET
from dao.annotation import get_ana_by_buc_func
from scripts.cache_manager import get_img_path_by_buc_func


def _remove_appledouble_files(target_dir):
    """清理 macOS 在外置盘上可能产生的 ._* 元数据文件。"""
    for file_name in os.listdir(target_dir):
        if file_name.startswith("._"):
            os.remove(os.path.join(target_dir, file_name))


def _get_image_size(image_path):
    """读取常见图片尺寸，避免 API 导出 XML 时额外依赖图像库。"""
    with open(image_path, "rb") as f:
        header = f.read(32)

        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return (
                int.from_bytes(header[16:20], "big"),
                int.from_bytes(header[20:24], "big"),
                3,
            )

        if header.startswith(b"\xff\xd8"):
            f.seek(2)
            while True:
                marker_start = f.read(1)
                if not marker_start:
                    break
                if marker_start != b"\xff":
                    continue
                marker = f.read(1)
                while marker == b"\xff":
                    marker = f.read(1)
                if marker in {b"\xc0", b"\xc1", b"\xc2", b"\xc3", b"\xc5", b"\xc6", b"\xc7", b"\xc9", b"\xca", b"\xcb", b"\xcd", b"\xce", b"\xcf"}:
                    f.read(3)
                    height = int.from_bytes(f.read(2), "big")
                    width = int.from_bytes(f.read(2), "big")
                    components = int.from_bytes(f.read(1), "big")
                    return width, height, components
                segment_length_bytes = f.read(2)
                if len(segment_length_bytes) != 2:
                    break
                segment_length = int.from_bytes(segment_length_bytes, "big")
                if segment_length < 2:
                    break
                f.seek(segment_length - 2, os.SEEK_CUR)

    return 0, 0, 3


def _indent_xml(elem, level=0):
    """给 ElementTree 输出补缩进，保持下载 XML 易读。"""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            _indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i


def build_annotation_xml(buc, func, image_path, annotations):
    """生成 Pascal VOC / LabelImg 兼容 XML 字符串。"""
    width, height, depth = _get_image_size(image_path)
    filename = f"{buc}_{func}.jpg"

    root = ET.Element("annotation")
    ET.SubElement(root, "folder").text = os.path.basename(os.path.dirname(image_path))
    ET.SubElement(root, "filename").text = filename
    ET.SubElement(root, "path").text = image_path

    source = ET.SubElement(root, "source")
    ET.SubElement(source, "database").text = "TurbineLabelStudio"

    size = ET.SubElement(root, "size")
    ET.SubElement(size, "width").text = str(width)
    ET.SubElement(size, "height").text = str(height)
    ET.SubElement(size, "depth").text = str(depth)

    ET.SubElement(root, "segmented").text = "0"

    for item in annotations or []:
        obj = ET.SubElement(root, "object")
        ET.SubElement(obj, "name").text = str(item.get("label") or "")
        ET.SubElement(obj, "pose").text = "Unspecified"
        ET.SubElement(obj, "truncated").text = "0"
        ET.SubElement(obj, "difficult").text = "1" if item.get("difficult") else "0"

        bndbox = ET.SubElement(obj, "bndbox")
        ET.SubElement(bndbox, "xmin").text = str(round(float(item["x1"])))
        ET.SubElement(bndbox, "ymin").text = str(round(float(item["y1"])))
        ET.SubElement(bndbox, "xmax").text = str(round(float(item["x2"])))
        ET.SubElement(bndbox, "ymax").text = str(round(float(item["y2"])))

    _indent_xml(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")


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

    from JoTools.txkjRes.deteRes import DeteRes

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
