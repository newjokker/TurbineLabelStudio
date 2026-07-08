
import os
from dao.uc_buc import add_uc_buc
from dao.wav_buc import get_buc_by_wave_md5
from JoTools.utils.CsvUtil import CsvUtil
from JoTools.utils.FileOperationUtil import FileOperationUtil
from JoTools.txkjRes.deteRes import DeteRes



csv_info = CsvUtil.read_csv_to_list("/Volumes/Jokker/Code/TurbineLabelStudio/search_result.csv")

file_info = {}
for each in csv_info[1:]:    
    file_name = each[0]
    tags = each[3]
    md5s = each[4]

    if each[2] == '6':
        file_info[file_name] = md5s.split(",")[0]


index = 0
for each in FileOperationUtil.re_all_file("/Volumes/Jokker/Code/TurbineLabelStudio/data/20260604_rename/Annotations", endswitch=[".xml"]):
    a = DeteRes(each)
    
    uc = FileOperationUtil.bang_path(each)[1]

    if a.img_path is None:
        continue
    
    img_name = a.img_path.split("\\")

    if len(img_name) > 0:
        img_name = img_name[-1].strip(".jpg")
        
        if img_name in file_info:
            # print(file_info[img_name])
            
            each_md5 = file_info[img_name]
            buc = get_buc_by_wave_md5(each_md5)
            add_uc_buc(uc=uc, buc=buc, func="wh_jzp_before_20260708")
            print(f"{uc}: {buc}")
            
            
        else:
            index += 1
            # print(f"{index}: 没找到对应的文件:{img_name}")
    else:
        index += 1
        # print("文件路径为空")
        continue



# info = {}
# for each in csv_info[1:]:
#     tags = each[3]
#     md5s = each[4]
    
#     if each[2] != '6':
#         continue
#     else:
#         buc = get_buc_by_wave_md5(md5s.split(",")[0])
#         uc = ""
        
#         if (uc is not None) and (buc is not None):
#             add_uc_buc(uc=uc, buc=buc, func="wh_jzp_before_20260708")

