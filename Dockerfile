FROM python:3.9.19
# FROM python:3.9.2

WORKDIR /usr/src/app

# install redis
RUN apt-get update || true
RUN apt-get install libglib2.0-0 -y && apt install libgl1-mesa-glx -y && apt-get install gcc -y || true
RUN apt-get install vim -y && apt-get install supervisor -y && apt install redis -y  
# RUN apt install wkhtmltopdf -y
RUN sed -i '69s/.*/bind 127.0.0.1/' /etc/redis/redis.conf

RUN pip install -i https://mirrors.aliyun.com/pypi/simple \
    sqlalchemy \
    fastapi \
    uvicorn \
    requests \
    fabric \
    numpy \
    soundfile \
    scipy

COPY ./ /usr/src/app

RUN mkdir -p /usr/src/app/logs
RUN chmod +x /usr/src/app/start_server.sh

RUN echo "alias ll='ls -l'" > ~/.bash_aliases

CMD ["./start_server.sh"]
