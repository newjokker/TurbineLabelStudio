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

* id(长整型), buc(string), func(string), x1(float), y1(float), x2(float), y2(float), label_id(int), difficult(bool), update_time(UTC), update_ID, update_reason(string), extra_info(JSON)  

* buc + func 能唯一确定一个图片，而不需要单独再去给图片编号

* uc, x1, y1, x2, y2, label, update_time, update_ID, update_reason 不能为空 

#### wav_uc 

* wav_buc: wave_md5(string), position_id(str), buc(string)

* 这边不对，应该是 BUC, 一组 wav 的集合，会有一个唯一的 BUC 的编码，直接使用自增(BUC_0000001), buc + func -> 图片 -> 生成 uc 

#### label

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

### 缓存管理

* wav 的缓存，目录：config.py 的 WAV_CACHE_DIR
* img 的缓存，目录：config.py 的 IMG_CACHE_DIR
* 给一个 wav 的 md5 在缓存中找到这个文件并返回对应的 path，如果没找到这个文件使用方法去下载
```python
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
```
* 下载后的 wav 存储方案，全部存储在 WAV_CACHE_DIR 文件夹下，命名就是 md5.wav

* 给一个 buc 和 func_name 返回对应的图片地址，要是没有找到这个图片的话 直接生成一个

* 生成 img 的方法 引用 /Volumes/Jokker/Code/TurbineLabelStudio/scripts/buc_func_util.py

```python
from dao.wav_buc import get_format_wave_md5_info_by_buc
from scripts.buc_func_util import get_buc_image_by_func


buc = "BUC_000086"

func_name = "wh_jzp_before_20260708"

md5_list = get_format_wave_md5_info_by_buc(buc=buc)

# 将 md5 找到对应的图片路径
wav_files = md5_list

res = get_buc_image_by_func(wav_files, func_name=func_name, save_path=f"{buc}_{func_name}.jpg")

```

* img 的命名方式为 f"func_name/{buc}_{func_name}.jpg" 

### 数据对齐

* 可以输出 jpg 和 对应的 xml 这样可以在 labelimg 里面进行标注，标注的结果也能映射回数据库

* 可以输出格式化的数据，六条 wav 文件放在一个文件夹中，文件夹的文件名是 buc，然后这个文件夹中还存放 xml 还有对应的 img 图片，xml 和 img 的名字一样，后缀不一样，都是 buc + func

### 项目存在的问题

* 虽然找到了 6 个 wav 文件，但是文件得到 mel 的流程还未精确还原，我得到的 mel 图和训练的图有少许差别

* 很多文件找不到 6 张图，之前标注也是根据四五个图进行标注的，现在不准备支持这样的图，当然可以在找不到图的情况下返回纯白色的图片但是需要约定一下

* 



