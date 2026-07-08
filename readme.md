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

