# 说明

### 使用场景

* 设计登录系统，只有有权限的人才能查看和修改
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

#### 人员登录表

* name(string), password(string), alias(string), end_time(UTC), role(string, enum)

* end_time 是停用的时间

* role 是角色
    * 观察者:只能查看不能修改导出
    * 编辑者:可以查看修改导出
    * 管理员:可以修改别的角色的权限，拥有别的角色的所有权限

