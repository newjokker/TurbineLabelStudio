# 说明

### 使用场景

* 查看标注
* 标注
* 关联原始 wav 与 uc
* 当前的 uc 交给图像进行入库
* 数据库支持输出 uc 格式的 json，支持查询 ucd，ucd json 格式是当前这个格式的子集
* 

### 表的设计

#### 主表

* md5(string), position_id(str), uc(string), x1(float), y1(float), x2(float), y2(float), label(string), update_time(UTC), update_ID, update_reason(string)  

* uc, x1, y1, x2, y2, label, update_time, update_ID, update_reason 不能为空

* 