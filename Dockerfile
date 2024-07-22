FROM python:3.11.9-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apk update && apk add --no-cache gcc musl-dev pkgconfig curl mysql-dev git

RUN curl -sSL -o argocd-linux-amd64 https://gitlab.snappcloud.io/amirreza.hosseini/argocd-linux/-/raw/main/argocd-linux-amd64 && install -m 555 argocd-linux-amd64 /usr/local/bin/argocd && rm argocd-linux-amd64

RUN export MYSQLCLIENT_CFLAGS=`pkg-config mysqlclient --cflags`
RUN export MYSQLCLIENT_LDFLAGS=`pkg-config mysqlclient --libs`

COPY requirements.txt .

RUN pip install --trusted-host repo.snapp.tech -i https://repo.snapp.tech/repository/pypi-all/simple/ --upgrade --no-cache-dir pip
RUN pip install --trusted-host repo.snapp.tech -i https://repo.snapp.tech/repository/pypi-all/simple/ --no-cache-dir --upgrade -r requirements.txt

COPY ./start.sh /start.sh
RUN chmod +x /start.sh

COPY ./gunicorn_conf.py /gunicorn_conf.py

COPY ./start-reload.sh /start-reload.sh
RUN chmod +x /start-reload.sh

ENV PYTHONPATH=/app

COPY ./app /app

COPY . .

RUN git rev-parse --short HEAD > app/git-head

RUN chgrp -R 0   /app && \
    chmod -R g=u /app

EXPOSE 80

CMD ["/start.sh"]
