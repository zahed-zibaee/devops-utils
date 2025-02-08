from fastapi import HTTPException
from app.core.config import settings
from app.core.logging import logging
import requests
import json
from datetime import datetime, timedelta


HEADERS = {
    'Authorization': f'Bearer {settings.GRAFANA_API_KEY}',
    'Content-Type': 'application/json'
}

def grafana_query(
        query,
        datasource_id = settings.GRAFANA_PROMETHEUS_DATABASE_ID,
        start = int((datetime.now() - timedelta(minutes=10)).timestamp()), 
        end = int((datetime.now() - timedelta(minutes=1)).timestamp()), 
        step = 30
    ):
    params = {
        'query': query,
        'start': start, 
        'end': end,  
        'step': step  
    }
    response = requests.get(
        settings.GRAFANA_URL + f"/api/datasources/proxy/{datasource_id}/api/v1/query_range", 
        headers=HEADERS, 
        params=params
    )
    if not response.ok \
        or not response.headers.get('Content-Type').startswith('application/json') \
        or response.json()['status'] != "success":
        logging.error("Grafana Request failed with status code: {}, error: {}".format(response.status_code, response.text))
        raise RuntimeError("Grafana Request failed with status code: {}".format(response.status_code))
    res = []
    for i in response.json()['data']['result']:
        labels = i['metric']
        values = i['values']
        res.append({'labels': labels, 'values': values})
    return res

def grafana_query_instant(
        query,
        datasource_id = settings.GRAFANA_PROMETHEUS_DATABASE_ID,
        time=int((datetime.now() - timedelta(minutes=1)).timestamp())
    ):
    params = {
        'query': query,  
        'time': time  
    }
    response = requests.get(
        settings.GRAFANA_URL + f"/api/datasources/proxy/{datasource_id}/api/v1/query", 
        headers=HEADERS, 
        params=params
    )
    if not response.ok \
        or not response.headers.get('Content-Type').startswith('application/json') \
        or response.json()['status'] != "success":
        logging.error("Grafana Request failed with status code: {}, error: {}".format(response.status_code, response.text))
        raise RuntimeError("Grafana Request failed with status code: {}".format(response.status_code))
    res = []
    for i in response.json()['data']['result']:
        labels = i['metric']
        value = i['value'][1]
        res.append({'labels': labels, 'value': value})
    return res