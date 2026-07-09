
from dao.label import add_label
import os
import xml.etree.ElementTree as ET
from JoTools.utils.FileOperationUtil import FileOperationUtil
from JoTools.txkjRes.deteRes import DeteRes
from dao.annotation import add_annotation
from JoTools.utils.CsvUtil import CsvUtil
from dao.wav_buc import get_buc_by_wave_md5


index = 0
for each in FileOperationUtil.re_all_file("/Volumes/Jokker/Code/TurbineLabelStudio/data/20260604", endswitch=[".xml"]):
    a = DeteRes(each)
    
    print(a.count_tags())
    




