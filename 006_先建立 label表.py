
from dao.label import add_label
import os
import xml.etree.ElementTree as ET
from JoTools.utils.FileOperationUtil import FileOperationUtil
from JoTools.txkjRes.deteRes import DeteRes
from dao.annotation import add_annotation
from JoTools.utils.CsvUtil import CsvUtil
from dao.wav_buc import get_buc_by_wave_md5
from dao.label import get_label_info_by_label

index = 0
for each in FileOperationUtil.re_all_file("/Volumes/Jokker/Code/TurbineLabelStudio/data/20260604", endswitch=[".xml"]):
    a = DeteRes(each)
    
    print(a.count_tags())
    
    for each in a:
        label_info = get_label_info_by_label(each.tag)
        if label_info is None:
            add_label(each.tag, des=None, update_by=None, extra_info=None)




