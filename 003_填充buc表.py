
from dao.wav_buc import add_wav_buc
from JoTools.utils.CsvUtil import CsvUtil


# {wave_md5: position_id}





csv_info = CsvUtil.read_csv_to_list("/Volumes/Jokker/Code/TurbineLabelStudio/search_result.csv")

for each in csv_info[1:]:
    print(each)
    
    tags = each[3]
    md5s = each[4]
    
    if each[2] != '6':
        continue
    
    print(tags)
    
    exit()







# add_wav_buc()









