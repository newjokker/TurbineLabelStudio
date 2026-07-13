# 说明

* 新入库数据的格式文档：http://pingcode.tuxingkeji.com:9443/wiki/spaces/SFB/pages/xvNX6oRM


### docker build

* docker build -t turbin_label_studio:v0.1.2 -f Dockerfile .

### docker 启动服务

* docker rm -f turbin_label_studio_server

* docker run --restart=always --name=turbin_label_studio_server  -v /etc/localtime:/etc/localtime  -v /usr/data/turbin_label_studio_log:/usr/data/fengji_sewrver_logs  -p 12502:12502  -it  turbin_label_studio:v0.1.2 /bin/bash 

* docker run --restart=always --name=turbin_label_studio_server  -v /etc/localtime:/etc/localtime  -v /usr/data/turbin_label_studio_log:/usr/data/fengji_sewrver_logs  -p 12502:12502  -d  turbin_label_studio:v0.1.2


* 服务默认放在 69 服务器上

* 对应的配置数据库放在容器外面，不随着容器重启而重启

### 版本

* v0.1
    * v0.1.1    开始项目
    * v0.1.2    在标注的时候可以对某一个标签进行评论，不标注的时候也能查看别人的评论

