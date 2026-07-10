
from dao.dataset import get_dataset_info_by_name
from dao.buc_dataset import get_bucs_not_assign_dataset, get_bucs_by_dataset_name


print(get_dataset_info_by_name("测试"))


info = get_bucs_not_assign_dataset()

print(len(info))





