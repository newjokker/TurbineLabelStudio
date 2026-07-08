# 说明

### 使用场景

* 设计登录系统，只有有权限的人才能查看和修改
* 查看标注
* 标注
* 关联原始 wav 与 uc
* 当前的 uc 交给图像进行入库
* 数据库支持输出 uc 格式的 json，支持查询 ucd，ucd json 格式是当前这个格式的子集
* 可以导出为 xml 在 labelimg 这样的软件打开，这个成熟的软件应该更加适合标注和修改

### 表的设计

* 表使用 sqlite 的方式存储在本地
* 表需要有一个备份计划，每天备份

#### 主表

* id(长整型), uc(string), x1(float), y1(float), x2(float), y2(float), label_id(int), difficult(bool), update_time(UTC), update_ID, update_reason(string), extra_info(JSON)  

* uc, x1, y1, x2, y2, label, update_time, update_ID, update_reason 不能为空 

#### wav_uc 

* wav_buc: wave_md5(string), position_id(str), buc(string)

* 这边不对，应该是 BUC, 一组 wav 的集合，会有一个唯一的 BUC 的编码，直接使用自增(BUC_0000001), buc + func -> 图片 -> 生成 uc 

#### uc_buc

* buc + func -> img_md5 -> uc 

* uc 是主键，func 是方法，使用字符串

* 增加数据的前提：
    * buc 需要在 wav_buc 表中存在
    * func 不能为空
    * uc 需要在符合 uc 的定义

#### 标签表

* id(int), label(string), update_time(UTC), des(string), update_by(string)

* des:是对这个标签的描述和标注的方法

* update_by 是谁编辑了这个标签

* 标签可以不断修改，关联的时候只要对应标签就行

* extra_info 其他的信息，使用 json 进行存储，方便扩展

#### 人员登录表

* id(int), name(string), password(string), alias(string), end_time(UTC), role(string, enum)

* end_time 是停用的时间

* role 是角色
    * 观察者:只能查看不能修改导出
    * 编辑者:可以查看修改导出
    * 管理员:可以修改别的角色的权限，拥有别的角色的所有权限

#### 日志表

* 记录谁在什么时间做了什么事情，将什么行修改为了什么，只限一个动作一个动作的修改，
* id(int), role_id(int), act(enum), table_name(string), update_time(UTC), change_info(json)  

### 界面的设计

* 在图上标记 xml 中的框
* 可以播放标记的一段音频（从对应的 6 个音频中选择其中一个位置的音频进行播放）
* 可以直接生成六个图的波形图
* 可以调整为编辑模式，在编辑的框中
* 可以将框出来的小图放在一个界面内进行对比，这样比较方便（创建一个缓存，子图的位置 + 标签 + UC 直接仿造 ucd 那一套就行了）

### 历史数据的处理

* 很多图的名字是有很多的信息的，根据时间进行筛选，然后找到对应的数据的文件名和对应的文件名进行核对即可

### 历史数据的处理步骤

* wav_md5 + sensor_code 入库到表中，得到 buc

* buc + fuc + uc 入库到 图像表中

* 


