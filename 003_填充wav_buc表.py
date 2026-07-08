
from dao.wav_buc import add_wav_buc
from JoTools.utils.CsvUtil import CsvUtil
import requests



def get_blade_info(md5):
    
    url = "http://192.168.3.69:11402/blade_file/search_by_md5"
    data = {
        "proj_name": "WindTurbineOnline",
        "md5": f"{md5}"
    }
    resp = requests.post(url, json=data)
    info = resp.json()
        
    if info["status"] == "success":
        tags = info["info"]["tags"]
        print(tags)
        code_1, code_2 = None, None
        if "叶片1" in tags:
            code_1 = "B1"
        if "叶片2" in tags:
            code_1 = "B2"
        if "叶片3" in tags:
            code_1 = "B3"
        if "测点A" in tags:
            code_2 = "A"
        if "测点B" in tags:
            code_2 = "B"
        
        if code_1 and code_2:
            return f"{code_1}{code_2}"
        else:
            return None
    else:
        return None



csv_info = CsvUtil.read_csv_to_list("/Volumes/Jokker/Code/TurbineLabelStudio/search_result.csv")


for each in csv_info[1:]:
    
    print("-"*100)
    # print(each)
    
    tags = each[3]
    md5s = each[4]
    
    
    if each[2] != '6':
        continue
    else:        
        dcu_info = {}
        sensor_code_list = []
        for each_md5 in md5s.split(","):     
            sensor_code = get_blade_info(each_md5)      
            dcu_info[each_md5] = sensor_code
            sensor_code_list.append(sensor_code)
    
    if ("B1A" in sensor_code_list) and ("B1B" in sensor_code_list) and ("B2A" in sensor_code_list) and ("B2B" in sensor_code_list) and ("B3A" in sensor_code_list) and ("B3B" in sensor_code_list):
        # print(dcu_info)

        try:        
            add_wav_buc(dcu_info)
        except:
            pass
        
    else:
        print("未找到全部的测点，跳过")



# add_wav_buc()









