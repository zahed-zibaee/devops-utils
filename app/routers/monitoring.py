from re import sub
from fastapi import APIRouter
from app.core.grafana import grafana_query, grafana_query_instant
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/devops-tools/v1/monitor/bool/debezium_connector_status_running_ratio_sink")
async def debezium_connector_status_running_ratio_sink():
    prometheus_query = 'min(debezium_kafka_connect_connector_task_status_metrics_running_ratio{connector=~".*-sink-connector"}) by (connector)'
    
    res = {}
    for metric in grafana_query_instant(prometheus_query):
        connector = metric['labels']['connector']
        db_name = connector_to_db_name(connector)
        value = metric['value']
        res[db_name] = True if value == '1' else False
    return res

@router.get("/devops-tools/v1/monitor/bool/debezium_connector_status_running_ratio_source")
async def debezium_connector_status_running_ratio_source():
    prometheus_query = 'min(debezium_kafka_connect_connector_task_status_metrics_running_ratio{connector=~".*-source-connector"}) by (connector)'
    
    res = {}
    for metric in grafana_query_instant(prometheus_query):
        connector = metric['labels']['connector']
        db_name = connector_to_db_name(connector)
        value = metric['value']
        res[db_name] = True if value == '1' else False
    return res

@router.get("/devops-tools/v1/monitor/bool/kafka_connectors_lag")
async def kafka_connectors_lag():
    prometheus_query = 'sum(kafka_consumergroup_lag) by (consumergroup)'
    
    def is_increasing_or_unchanged(numbers):
        for i in range(1, len(numbers)):
            if numbers[i] < numbers[i - 1]:
                return False
            if numbers[i] <= 0:  
                return False
        return True 
    
    metrics = grafana_query(
            prometheus_query, 
            start = int((datetime.now() - timedelta(minutes=30)).timestamp())
        )
    
    res = {}
    for metric in metrics:
        connector = metric['labels']['consumergroup']
        db_name = connector_to_db_name(connector)
        values = [int(i[1]) for i in metric['values']]
        res[db_name] = False if is_increasing_or_unchanged(values) else True
    
    return res

def connector_to_db_name(connector_name):
    consumergroup_lstriped = sub(r'^connect-', '', connector_name)
    connector_lstriped = sub(r'^(pg-|mysql-)', '', consumergroup_lstriped)
    connector_striped = sub(r'-jdbc-\w+-connector$', '', connector_lstriped)
    db_name = connector_striped.capitalize()
    return db_name