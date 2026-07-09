# -*- coding: utf-8 -*-
"""验证过的数据和标签入库工具。"""

import sys
import os
import xml.etree.ElementTree as ET
from JoTools.utils.FileOperationUtil import FileOperationUtil
from JoTools.txkjRes.deteRes import DeteRes
from dao.annotation import add_annotation
from JoTools.utils.CsvUtil import CsvUtil
from dao.wav_buc import get_buc_by_wave_md5
from dao.label import get_label_info_by_label


csv_info = CsvUtil.read_csv_to_list("/Volumes/Jokker/Code/TurbineLabelStudio/search_result.csv")

file_info = {}
for each in csv_info[1:]:    
    file_name = each[0]
    tags = each[3]
    md5s = each[4]

    if each[2] == '6':
        file_info[file_name] = md5s.split(",")[0]



index = 0
for each in FileOperationUtil.re_all_file("/Volumes/Jokker/Code/TurbineLabelStudio/data/20260604", endswitch=[".xml"]):
    a = DeteRes(each)
    
    file_name = FileOperationUtil.bang_path(each)[1]
    
    # 新增函数，如果标签没有定义就报错
    # 新增函数，如果 update_id 没定义就报错
    # 新增函数，根据 tag_name 找到 tag_id, 这个直接在函数里面实现吧
    

    
    if file_name in file_info:
        each_md5 = file_info[file_name]
        buc = get_buc_by_wave_md5(each_md5)
        if buc is None:
            print(f"buc 没入库:{file_name}")
            
        else:
            
            for obj in a:
                
                label_info = get_label_info_by_label(obj.tag)
                
                if label_info is not None:
                    label_id = label_info["id"]
                    add_annotation(buc=buc, func="wh_jzp_before_20260708", x1=obj.x1, x2=obj.x2, y1=obj.y1, y2=obj.y2, label_id=label_id, update_id=1, difficult=False, extra_info=None)
                else:
                    print(f"label 未注册:{obj.tag}")


