FROM registry.teh-1.snappcloud.io/fra-1/library/python:3.9

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--reload"]