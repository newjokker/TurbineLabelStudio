

from scripts.format_transform import save_img_and_xml
from dao.wav_buc import get_all_buc_list

buc_list = get_all_buc_list()

for each in buc_list:
    save_img_and_xml(each, "wh_jzp_before_20260708", "/Volumes/Jokker/Code/TurbineLabelStudio/data/save_res")


