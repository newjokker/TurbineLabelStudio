
from dao.dataset import get_dataset_info_by_name, get_all_datasets
from dao.buc_dataset import get_bucs_not_assign_dataset, get_bucs_by_dataset_name, add_buc_dataset


dataset_name = "for_ldq"

dataset_info = get_dataset_info_by_name(dataset_name)
dataset_id = dataset_info["id"]

# # info = get_bucs_not_assign_dataset()

# # print(len(info))


# res = get_all_datasets()


# print(res)


# info = get_bucs_not_assign_dataset()

# for each_buc in info[:50]:
    
#     add_buc_dataset(dataset_id=dataset_id, buc=each_buc)

print(get_bucs_by_dataset_name(dataset_name))



