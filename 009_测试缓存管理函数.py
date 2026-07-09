

from scripts.cache_manager import get_img_path_by_buc_func, get_wav_path_by_md5



wav_path = get_wav_path_by_md5("a52b0b7744c74d0368c9b9b5f51cbe14")

img_path = get_img_path_by_buc_func("BUC_000087", "wh_jzp_before_20260708")

print(wav_path)

print(img_path)



