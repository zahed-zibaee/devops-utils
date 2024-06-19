from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.core.kubernetes import create_job, job_status
from app.core.logging import logger
from app.core.config import settings
from app.core.kubernetes import client as k8s_client
from app.schemas.main import Job


router = APIRouter()

@router.post("/devops-tools/v1/kubernetes/jobs/aggregation/create")
async def create_aggregation_schema_job(job: Job):
    if job.type == "schema":
        job_name = settings.JOB_AG_SYNC_NAME+"-schema"
        COMMAND = "/backup/backup-schema.sh"
        IMAGE = settings.JOB_AG_SYNC_IMAGE_SCHEMA
    elif job.type == "tables":
        job_name = settings.JOB_AG_SYNC_NAME+"-tables"
        COMMAND = "/backup/backup-tables.sh"
        IMAGE = settings.JOB_AG_SYNC_IMAGE_TABLES
    else:
        logger.error("Could not identify job name.")
        raise HTTPException(status_code=404, detail='Job type no found!')
    ENV = [k8s_client.V1EnvVar(name='USERNAME', value=settings.DB_PG_AG_USERNAME),
           k8s_client.V1EnvVar(name='HOST', value=settings.DB_PG_AG_HOST),
           k8s_client.V1EnvVar(name='FILENAME', value=settings.JOB_AG_SYNC_BK_FILENAME),
           k8s_client.V1EnvVar(name='STAGING_HOST', value=settings.DB_PG_AG_STAGING_HOST),
           k8s_client.V1EnvVar(name='PASSWORD', value_from=k8s_client.V1EnvVarSource(
               secret_key_ref=k8s_client.V1SecretKeySelector(
                   name=settings.DB_PG_AG_SECRET_NAME,
                   key='PASSWORD'
               )
           )),
           k8s_client.V1EnvVar(name='STAGING_PASSWORD', value_from=k8s_client.V1EnvVarSource(
               secret_key_ref=k8s_client.V1SecretKeySelector(
                   name=settings.DB_PG_AG_SECRET_NAME,
                   key='STAGING_PASSWORD'
               )
           ))]
    volume = k8s_client.V1Volume(
        name="backupdir",
        persistent_volume_claim=k8s_client.V1PersistentVolumeClaimVolumeSource(
            claim_name=job_name
        )
    )
    container = k8s_client.V1Container(
        name=settings.JOB_AG_SYNC_NAME,
        image=IMAGE,
        image_pull_policy="IfNotPresent",
        command=["/bin/sh", "-c", COMMAND],
        env=ENV,
        volume_mounts=[k8s_client.V1VolumeMount(
            mount_path="/backup/dump",
            name="backupdir"
        )],
        resources=k8s_client.V1ResourceRequirements(
            requests={"cpu" : settings.JOB_CPU_REQUEST, "memory" : settings.JOB_MEMORY_REQUEST},
            limits={"cpu" : settings.JOB_CPU_LIMIT, "memory" : settings.JOB_MEMORY_LIMIT}
        )
    )
    template = k8s_client.V1PodTemplateSpec(
        metadata=k8s_client.V1ObjectMeta(labels={
            "snapp.supply/app-name": "aggregation-sync",
            "snapp.supply/app-instance": "aggregation-backup-schema",
            "snapp.supply/app-type": "backup",
            "snapp.supply/app-environment" : settings.JOB_AG_SYNC_SOURCE_NAMESPACE
            }),
        spec=k8s_client.V1PodSpec(restart_policy="Never",
                              containers=[container],
                              volumes=[volume])
        )
    try:
        create_job(job_name, settings.JOB_AG_SYNC_SOURCE_NAMESPACE, template)
    except Exception as e:
        logger.error(f"Error occured during creating job: {str(e)}")
        raise HTTPException(status_code=503, detail='Job creation failed.')
    
    return JSONResponse({"Status" : "Created"})

@router.get("/devops-tools/v1/kubernetes/jobs/aggregation/status/")
async def aggregation_job_status(job_name: str):
    status = job_status(job_name, settings.JOB_AG_SYNC_SOURCE_NAMESPACE)
    if status not in range(200, 299) and type(status) == int:
        raise HTTPException(status_code=503, detail=f'Failed to get the job status. {str(status)}')
    return JSONResponse(status)
