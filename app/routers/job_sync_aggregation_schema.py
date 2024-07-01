from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from kubernetes import client as k8s_client

from app.core.kubernetes import create_job, job_status
from app.core.logging import logger
from app.core.config import settings
from app.core.redis import is_locked, lock, unlock
from app.schemas.main import Job


router = APIRouter()




def job_time():
    return datetime.now().strftime("%Y%m%d%H%M%S")

@router.post("/devops-tools/v1/kubernetes/jobs/aggregation/create")
async def create_aggregation_schema_job(job: Job):
    if job.type == "views":
        job_name = settings.JOB_AG_SYNC_NAME+"-view"
        COMMAND = "/backup/backup-views.sh"
        IMAGE = settings.JOB_AG_SYNC_IMAGE_VIEWS
    elif job.type == "tables":
        job_name = settings.JOB_AG_SYNC_NAME+"-tables"
        COMMAND = "/backup/backup-tables.sh"
        IMAGE = settings.JOB_AG_SYNC_IMAGE_TABLES
    else:
        logger.error("Could not identify job name.")
        raise HTTPException(status_code=404, detail='Job type no found!')

    if not await is_locked(job_name):
        await lock(job_name, 60)

        SECRET_ENV = k8s_client.V1EnvFromSource(
            secret_ref = k8s_client.V1SecretEnvSource(
            name=settings.JOB_AG_SECRET
            )
        )

        CONFIG_MAP_ENV = k8s_client.V1EnvFromSource(
            config_map_ref = k8s_client.V1ConfigMapEnvSource(
            name=settings.JOB_AG_CONFIG_MAP
            )
        )

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
            env_from=[SECRET_ENV, CONFIG_MAP_ENV],
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

        job_name = job_name+"-"+job_time()
        try:
            create_job(job_name, settings.JOB_AG_SYNC_SOURCE_NAMESPACE, template)
        except Exception as e:
            logger.error(f"Error occured during creating job: {str(e)}")
            raise HTTPException(status_code=503, detail='Job creation failed.')

        return JSONResponse({"Status" : "Created",
                             "Job" : job_name})
    else:
        raise HTTPException(status_code=409, detail="Operation is already in progress")

@router.get("/devops-tools/v1/kubernetes/jobs/aggregation/status/")
async def aggregation_job_status(job_name: str):
    status = job_status(job_name, settings.JOB_AG_SYNC_SOURCE_NAMESPACE)
    if status not in range(200, 299) and type(status) == int:
        raise HTTPException(status_code=503, detail=f'Failed to get the job status. {str(status)}')
    if 'Last Transition Time' in status:
        last_transition_time_str = status['Last Transition Time'].isoformat()
        status['Last Transition Time'] = last_transition_time_str
    if ('Succeeded' in status or 'Failed' in status):
        for suffix in ["view", "tables"]:
            lock_name = f"{settings.JOB_AG_SYNC_NAME}-{suffix}"
            if await is_locked(lock_name):
                logger.info(f'Unlocking job: {lock_name}')
                await unlock(lock_name)
                return
        
    return JSONResponse(status)
