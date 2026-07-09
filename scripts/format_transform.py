
import os
import shutil
from dao.wav_buc import get_all_buc_list
from dao.annotation import get_ana_by_buc_func
from scripts.cache_manager import get_img_path_by_buc_func, get_wav_path_by_md5
from JoTools.txkjRes.deteRes import DeteRes


# 将数据库中的标注修改为 xml 格式，直接调用 JoTools 模块即可
def save_img_and_xml(buc, func, save_dir):
    
    img_path = get_img_path_by_buc_func(buc=buc, func_name=func)
    if img_path is None:
        raise ValueError( f"未找到图片路径:{buc}, {func}")
    
    ana_info = get_ana_by_buc_func(buc=buc, func_name=func)
    
    if ana_info is None:
        return 
    
    dete_res = DeteRes()
    for obj in ana_info:
        dete_res.add_obj(x1=obj["x1"], y1=obj["y1"], x2=obj["x2"], y2=obj["y2"], tag=obj["label"])
        
    xml_save_path = os.path.join(save_dir, f"{buc}_{func}.xml")
    img_save_path = os.path.join(save_dir, f"{buc}_{func}.jpg")
    
    dete_res.save_to_xml(xml_save_path)
    
    shutil.copy(img_path, img_save_path)






