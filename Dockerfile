#FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11
FROM registry.teh-1.snappcloud.io/fra-1/tiangolo/uvicorn-gunicorn-fastapi:python3.11

WORKDIR /app

RUN apt-get update && apt-get install -y default-libmysqlclient-dev pkg-config

RUN curl -sSL -o argocd-linux-amd64 https://gitlab.snappcloud.io/amirreza.hosseini/argocd-linux/-/raw/main/argocd-linux-amd64 && install -m 555 argocd-linux-amd64 /usr/local/bin/argocd && rm argocd-linux-amd64

RUN export MYSQLCLIENT_CFLAGS=`pkg-config mysqlclient --cflags`
RUN export MYSQLCLIENT_LDFLAGS=`pkg-config mysqlclient --libs`

COPY requirements.txt .

RUN pip install --upgrade --no-cache-dir pip &&  pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

RUN chgrp -R 0   /app && \
    chmod -R g=u /app
