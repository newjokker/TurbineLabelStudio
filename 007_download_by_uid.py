
import os
import requests
from dao.wav_buc import get_wave_md5_info_by_buc

    
def load_wav_by_md5(md5, save_dir):
    file_type = ".wav"
    url = "http://192.168.3.69:11402/file/download/" + md5 + file_type
    resp = requests.get(url)
    if resp.status_code == 200:
        with open(os.path.join(save_dir, f"{md5}.wav"), "wb") as f:
            f.write(resp.content)
        return True
    else:
        return False
        

def get_wav_from_buc(buc, save_dir):
    
    md5_position_info = get_wave_md5_info_by_buc(buc)

    save_dir = os.path.join(save_dir, buc)
    os.makedirs(save_dir, exist_ok=True)

    if md5_position_info is not None:
        
        for each in md5_position_info:
            load_wav_by_md5(each[0], save_dir)
        

get_wav_from_buc("BUC_000086", "/Volumes/Jokker/Code/TurbineLabelStudio/data/test")