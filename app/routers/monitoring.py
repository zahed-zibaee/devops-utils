from re import sub
from fastapi import APIRouter, HTTPException
from app.core.grafana import grafana_query, grafana_query_instant
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/devops-tools/v1/monitor/bool/debezium_connector_status_running_ratio_sink")
async def debezium_connector_status_running_ratio_sink():
    prometheus_query = 'min(debezium_kafka_connect_connector_task_status_metrics_running_ratio{connector=~".*-sink-connector"}) by (connector)'
    
    
    try:
        metrics = grafana_query_instant(prometheus_query)
    except Exception as e:
        return HTTPException(f'{e}')
    
    res = {}
    for metric in metrics:
        connector = metric['labels']['connector']
        db_name = connector_to_db_name(connector)
        value = metric['value']
        res[db_name] = True if value == '1' else False
    return res

@router.get("/devops-tools/v1/monitor/bool/debezium_connector_status_running_ratio_source")
async def debezium_connector_status_running_ratio_source():
    prometheus_query = 'min(debezium_kafka_connect_connector_task_status_metrics_running_ratio{connector=~".*-source-connector"}) by (connector)'
    
    try:
        metrics = grafana_query_instant(prometheus_query)
    except Exception as e:
        return HTTPException(f'{e}')
    
    res = {}
    for metric in metrics:
        connector = metric['labels']['connector']
        db_name = connector_to_db_name(connector)
        value = metric['value']
        res[db_name] = True if value == '1' else False
    return res

@router.get("/devops-tools/v1/monitor/bool/kafka_connectors_lag")
async def kafka_connectors_lag():
    prometheus_query = 'sum(kafka_consumergroup_lag) by (consumergroup, topic)'
    
    def is_increasing_or_unchanged(numbers):
        for i in range(1, len(numbers)):
            if numbers[i] < numbers[i - 1]:
                return False
            if numbers[i] <= 0:  
                return False
        return True 

    try:
        metrics = grafana_query(
            prometheus_query, 
            start = int((datetime.now() - timedelta(minutes=20)).timestamp()), 
            end = int((datetime.now() - timedelta(minutes=1)).timestamp()), 
            step = 30
        )
    except Exception as e:
        return HTTPException(f'{e}')
    
    res = {}
    for metric in metrics:
        table = metric['labels']['topic']
        values = [int(i[1]) for i in metric['values']]
        res[topic_to_table_name(table)] = False if is_increasing_or_unchanged(values) else True
    
    return res

def connector_to_db_name(connector_name):
    consumergroup_lstriped = sub(r'^connect-', '', connector_name)
    connector_lstriped = sub(r'^(pg-|mysql-)', '', consumergroup_lstriped)
    connector_striped = sub(r'-jdbc-\w+-connector$', '', connector_lstriped)
    db_name = connector_striped.capitalize()
    return db_name

def topic_to_table_name(topic_name):
    try:
        db_table_list = topic_name.split("_",1)
        db = db_table_list[0]
        table = db_table_list[1]
        return f"{db}: {table}"
    except:
        return topic_name
        
    
