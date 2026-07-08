
# -*- coding: utf-8 -*-
"""验证过的数据和标签入库工具。"""
import sys
import os
import xml.etree.ElementTree as ET
from JoTools.utils.FileOperationUtil import FileOperationUtil
from JoTools.txkjRes.deteRes import DeteRes


def _node_text(node, xpath, *, default=None, required=True):
    """读取 XML 节点文本。"""
    child = node.find(xpath)
    if child is None or child.text is None:
        if required:
            raise ValueError(f"XML 缺少字段: {xpath}")
        return default
    text = child.text.strip()
    if text == "" and required:
        raise ValueError(f"XML 字段为空: {xpath}")
    return text if text != "" else default


def _parse_number(text, field_name):
    """坐标优先返回 int，遇到小数时返回 float。"""
    try:
        value = float(text)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"XML 坐标字段不是数字: {field_name}={text}") from exc
    return int(value) if value.is_integer() else value


def _parse_difficult(text):
    """解析 difficult 字段，兼容 0/1/true/false。"""
    value = str(text).strip().lower()
    if value in ("1", "true", "yes"):
        return 1
    if value in ("0", "false", "no", ""):
        return 0
    raise ValueError(f"XML difficult 字段不合法: {text}")


def parse_annotation_xml(xml_path):
    """解析 LabelImg/Pascal VOC XML。

    Returns:
        [[x1, y1, x2, y2, label, diffcult], ...]
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    result = []

    for index, obj in enumerate(root.findall("object"), start=1):
        label = _node_text(obj, "name")
        difficult = _parse_difficult(_node_text(obj, "difficult", default="0", required=False))
        box = obj.find("bndbox")
        if box is None:
            raise ValueError(f"第 {index} 个 object 缺少 bndbox")

        x1 = _parse_number(_node_text(box, "xmin"), "xmin")
        y1 = _parse_number(_node_text(box, "ymin"), "ymin")
        x2 = _parse_number(_node_text(box, "xmax"), "xmax")
        y2 = _parse_number(_node_text(box, "ymax"), "ymax")
        result.append([x1, y1, x2, y2, label, difficult])

    return result


if __name__ == "__main__":
    
    # （1）将 csv 的信息放到字典中去
    
    # （2）遍历 xml 挑出原始的文件名，
    

    for each in FileOperationUtil.re_all_file("/Volumes/Jokker/Code/TurbineLabelStudio/data/20260604_rename/Annotations", endswitch=[".xml"]):
        a = DeteRes(each)

        img_name = a.img_path.split("\\")
    
        if len(img_name) > 0:
            img_name = img_name[-1]
        else:
            continue

        img_path = os.path.join("/Volumes/Jokker/Code/TurbineLabelStudio/data/20260604", img_name)
        
        if os.path.exists(img_path):
            print(img_path)            

        

