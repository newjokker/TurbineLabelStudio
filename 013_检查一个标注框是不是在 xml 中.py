
from JoTools.txkjRes.deteRes import DeteRes
from JoTools.utils.FileOperationUtil import FileOperationUtil



xml_dir = "/Users/jokkerling/Desktop/20260604"

for each_xml in FileOperationUtil.re_all_file(xml_dir, endswitch=[".xml"]):
    
    dete_res = DeteRes(each_xml)
    for each in dete_res:
        if (each.x1 == 862) and (each.y1 == 1) and (each.x2 == 884 and each.y2 == 401):
            print(each_xml)
            



