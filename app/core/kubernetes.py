from fastapi import HTTPException
from app.core.config import settings
from kubernetes import client
from datetime import datetime
from kubernetes.client.rest import ApiException
from app.core.logging import logger
from fastapi.responses import JSONResponse


configuration = client.Configuration()

configuration.api_key['authorization'] = settings.API_TOKEN
configuration.api_key_prefix['authorization'] = 'Bearer'
configuration.host = settings.API_URL


client.Configuration.set_default(configuration)
v1 = client.BatchV1Api()



def create_job(job_name, job_namespace, job_template):

    job_spec = client.V1JobSpec(
        template=job_template,
        backoff_limit=4
    )

    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=job_name+"-"+job_time()),
        spec=job_spec
    )

    try:
        api_response = v1.create_namespaced_job(
            body=job,
            namespace=job_namespace)
    except ApiException as e:
        logger.error(f"APIException occured during creating job: {str(e)}")
    except Exception as e:
        logger.error(f"Error occured during creating job: {str(e)}")

    logger.info("Job created. Status='%s'" % str(api_response.status))


    return api_response.status



def job_time():
    now = datetime.now()
    formatted_datetime = now.strftime("%Y%m%d%H%M%S")

    return formatted_datetime




def job_status(job_name, namespace):
    try:
        job = v1.read_namespaced_job_status(name=job_name, namespace=namespace)
        
        data = {"Job name" : job.metadata.name,
                "Namespace" : job.metadata.namespace}
    
        if job.status.conditions:
            for condition in job.status.conditions:
                data["Type"] = condition.type
                data["Status"] = condition.status
                data["Reason"] = condition.reason
                data["Message"] = condition.message
                data["Last Transition Time"] = condition.last_transition_time
        else:
            logger.info("No conditions available for this job.")

        if job.status.active:
            data["Active"] = job.status.active
        if job.status.succeeded:
            data["Succeeded"] = job.status.succeeded
        if job.status.failed:
            data["Failed"] = job.status.failed
        return data
    
    except ApiException as e:
        logger.error(f"Exception when reading job status: {e}")
        return e.status

