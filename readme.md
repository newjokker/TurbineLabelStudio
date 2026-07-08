# 说明

* 新入库数据的格式文档：http://pingcode.tuxingkeji.com:9443/wiki/spaces/SFB/pages/xvNX6oRM


### docker build

* docker build -t fengji_data_server:v0.1.6 -f Dockerfile .

### docker 启动服务

* docker rm -f fengji_data_upload_server

* docker run --restart=always --name=fengji_data_upload_server  -v /etc/localtime:/etc/localtime  -v /usr/data/fengji_data_server_database:/usr/data/fengji_sewrver_logs  -p 12501:12501  -it  fengji_data_server:v0.1.6 /bin/bash 

* docker run --restart=always --name=fengji_data_upload_server  -v /etc/localtime:/etc/localtime  -v /usr/data/fengji_data_server_database:/usr/data/fengji_sewrver_logs  -p 12501:12501  -d  fengji_data_server:v0.1.6


* 服务默认放在 69 服务器上

* 对应的配置数据库放在容器外面，不随着容器重启而重启

### 版本

* v0.1
    * v0.1.1    

### 服务开始结束

启动服务：

```bash
./start_server.sh
```

停止服务：

```bash
./stop_server.sh
```

### 下载失败重试控制

下载任务仍会对单个文件做短重试，但为了避免远程端口不可达时不断刷失败日志，额外增加两层保护：

* `DOWNLOAD_MAX_CONSECUTIVE_FAILURES`：同一风机连续下载失败达到该值后，停止本轮该风机处理，默认 `3`
* `DOWNLOAD_FAILED_RETRY_COOLDOWN_SECONDS`：下载失败文件的冷却时间，冷却期内不重复下载，默认 `6 * 60 * 60`

属性上传失败只记录到 `info_upload_status=failed` 和日志中，不计入整体文件失败，也不会进入失败重试队列。

### 对外查询接口

服务地址默认：

```text
http://192.168.3.69:12501
```

#### 1. ID 关系查询

对应页面里的“ID 关系查询”，支持 `wind_farm_id`、`turbine_id`、`sensor_id`。

```http
GET /api/query/relation?type=turbine_id&value=TB001
GET /api/query/relation?type=wind_farm_id&value=WF001
GET /api/query/relation?type=sensor_id&value=SI0001
```

返回字段：

```json
{
  "query": {"type": "turbine_id", "value": "TB001"},
  "wind_farm": {},
  "turbine": {},
  "sensor": null,
  "turbines": [],
  "sensors": []
}
```

#### 2. 关键词查询

对应页面里的“关键词查询”，支持查询 `wind_farm`、`turbine`、`sensor`、`download_info` 四类数据。

```http
GET /api/query/keyword?level=wind_farm&keyword=xxx
GET /api/query/keyword?level=turbine&keyword=xxx
GET /api/query/keyword?level=sensor&keyword=xxx
GET /api/query/keyword?level=download_info&keyword=xxx
```

返回字段：

```json
{
  "query": {"level": "sensor", "keyword": "xxx"},
  "fields": ["sensor_id", "sensor_code", "hc_id", "turbine_id", "position_id", "is_activate"],
  "rows": []
}
```

#### 3. hc_id 查询

根据指定级别和 `hc_id` 精确查询，支持查询 `wind_farm`、`turbine`、`sensor` 三类数据。

```http
GET /api/query/hc_id?level=wind_farm&hc_id=HC001
GET /api/query/hc_id?level=turbine&hc_id=HC-TB001
GET /api/query/hc_id?level=sensor&hc_id=HC-SI001
```

返回字段：

```json
{
  "query": {"level": "sensor", "hc_id": "HC-SI001"},
  "fields": ["sensor_id", "sensor_code", "hc_id", "turbine_id", "position_id", "is_activate"],
  "rows": []
}
```

#### 4. 单表查询

查询风场：

```http
GET /api/query/wind_farm?wind_farm_id=WF001
```

查询风机：

```http
GET /api/query/turbine?turbine_id=TB001
GET /api/query/turbine?wind_farm_id=WF001
```

查询传感器：

```http
GET /api/query/sensor?sensor_id=SI0001
GET /api/query/sensor?sensor_code=xxx
GET /api/query/sensor?turbine_id=TB001
```

查询下载配置：

```http
GET /api/query/download_info
GET /api/query/download_info?turbine_id=TB001
GET /api/query/download_info?id=1
```

#### 5. 获取全部配置

获取所有风场：

```http
GET /api/wind_farms
```

获取所有风机：

```http
GET /api/turbines
```

获取所有传感器：

```http
GET /api/sensors
```

获取所有下载配置：

```http
GET /api/download_info
```

返回字段：

```json
{
  "rows": []
}
```

导出所有风场、风机、传感器、下载配置之间的关系，返回结构可作为 `scripts/bulk_create_farm.py` 的输入：

```http
GET /api/export/farm_config
```

返回字段：

```json
{
  "wind_farms": [
    {
      "hc_id": "HC-WF-001",
      "name": "示例风场",
      "turbines": [
        {
          "hc_id": "HC-TB-001",
          "name": "1号风机",
          "download_info": {
            "ssh_addr": "22",
            "download_flag": 3
          },
          "sensors": [
            {
              "sensor_code": "TB001-S001",
              "hc_id": "HC-SI-001",
              "position_id": "B1A",
              "is_activate": true
            }
          ]
        }
      ]
    }
  ]
}
```

如果一台风机有多条下载配置，`download_info` 会导出为数组；只有一条时仍保持对象格式，方便兼容旧脚本输入。

### 对外新增接口

新增接口使用 JSON 请求体，成功时返回 `201`，返回字段为新增后的 `row`。

#### 1. 新增风场

```http
POST /api/wind_farms
Content-Type: application/json
```

请求体：

```json
{
  "hc_id": "HC001",
  "name": "示例风场"
}
```

返回示例：

```json
{
  "row": {
    "wind_farm_id": "WF001",
    "hc_id": "HC001",
    "name": "示例风场"
  }
}
```

#### 2. 新增风机

`wind_farm_id` 必须是已存在的风场 ID。

```http
POST /api/turbines
Content-Type: application/json
```

请求体：

```json
{
  "hc_id": "HC-TB001",
  "wind_farm_id": "WF001",
  "name": "示例风机"
}
```

返回示例：

```json
{
  "row": {
    "turbine_id": "TB001",
    "hc_id": "HC-TB001",
    "wind_farm_id": "WF001",
    "name": "示例风机"
  }
}
```

#### 3. 新增传感器

`turbine_id` 必须是已存在的风机 ID，`sensor_code` 不能为空且不能重复。

```http
POST /api/sensors
Content-Type: application/json
```

请求体：

```json
{
  "turbine_id": "TB001",
  "sensor_code": "SENSOR001",
  "hc_id": "HC-SI001",
  "position_id": "P001",
  "is_activate": true
}
```

返回示例：

```json
{
  "row": {
    "sensor_id": "SI0001",
    "sensor_code": "SENSOR001",
    "hc_id": "HC-SI001",
    "turbine_id": "TB001",
    "position_id": "P001",
    "is_activate": true
  }
}
```

#### 4. 新增下载配置

`turbine_id` 必须是已存在的风机 ID。

```http
POST /api/download_info
Content-Type: application/json
```

请求体：

```json
{
  "turbine_id": "TB001",
  "ssh_addr": "22",
  "download_flag": 1
}
```

返回示例：

```json
{
  "row": {
    "id": 1,
    "turbine_id": "TB001",
    "ssh_addr": "22",
    "download_flag": 1
  }
}
```

`download_info` 使用自增 `id` 作为主键，同一个 `turbine_id` 可以新增多条记录，对应不同的 `ssh_addr` 和 `download_flag`。

新增失败时返回 `400`：

```json
{
  "error": "create failed"
}
```

### 批量新增一个风场的配置

如果要一次性新增一个风场、该风场下所有风机、每台风机下所有传感器，可以使用脚本：

```bash
python3 scripts/bulk_create_farm.py 
```

信息组织方式使用嵌套 JSON：

`download_info` 可以写成单个对象，也可以写成对象数组；脚本会按顺序为同一台风机创建多条下载配置。

```json
{
  "wind_farm": {
    "hc_id": "HC-WF-001",
    "name": "示例风场",
    "turbines": [
      {
        "hc_id": "HC-TB-001",
        "name": "1号风机",
        "download_info": {
          "ssh_addr": "22",
          "download_flag": 1
        },
        "sensors": [
          {
            "sensor_code": "TB001-S001",
            "hc_id": "HC-SI-001",
            "position_id": "P001",
            "is_activate": true
          }
        ]
      }
    ]
  }
}
```

脚本会按下面顺序调用接口：

1. 先调用 `POST /api/wind_farms` 新增风场，拿到返回的 `wind_farm_id`
2. 再调用 `POST /api/turbines` 新增每台风机，自动把上一步的 `wind_farm_id` 放进请求体
3. 再调用 `POST /api/sensors` 新增每个传感器，自动把对应风机返回的 `turbine_id` 放进请求体
4. 如果风机里配置了 `download_info`，会调用 `POST /api/download_info`，自动把对应风机返回的 `turbine_id` 放进请求体

完整示例见：

```text
examples/farm_config.example.json
```
