# -*- coding: utf-8 -*-
"""验证过的数据和标签入库工具。"""

import sys
import os
import xml.etree.ElementTree as ET
from JoTools.utils.FileOperationUtil import FileOperationUtil
from JoTools.txkjRes.deteRes import DeteRes
from dao.annotation import add_annotation


index = 0
for each in FileOperationUtil.re_all_file("/Volumes/Jokker/Code/TurbineLabelStudio/data/20260604_rename/Annotations", endswitch=[".xml"]):
    a = DeteRes(each)
    
    uc = FileOperationUtil.bang_path(each)[1]
    
    # 新增函数，如果标签没有定义就报错
    # 新增函数，如果 update_id 没定义就报错
    # 新增函数，根据 tag_name 找到 tag_id, 这个直接在函数里面实现吧
    
    for obj in a:
        add_annotation(uc=uc, x1=obj.x1, x2=obj.x2, y1=obj.y1, y2=obj.y2, label_id=0, update_id=0, difficult=False, extra_info=None)
        

