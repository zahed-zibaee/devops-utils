from fastapi import APIRouter, HTTPException
from app.core.kubernetes import create_job, job_status
from fastapi.responses import JSONResponse
from app.core.logging import logger
from app.core.config import settings
from kubernetes import client



router = APIRouter()


@router.post("/devops-tools/v1/kubernetes/jobs/aggregation/create")
async def create_aggregation_job():
    ENV = [client.V1EnvVar(name='USERNAME', value=settings.AG_DB_USERNAME),
           client.V1EnvVar(name='HOST', value=settings.AG_DB_HOST),
           client.V1EnvVar(name='FILENAME', value=settings.AG_FILENAME),
           client.V1EnvVar(name='STAGING_HOST', value=settings.AG_DB_STAGING_HOST),
           client.V1EnvVar(name='PASSWORD', value_from=client.V1EnvVarSource(
               secret_key_ref=client.V1SecretKeySelector(
                   name=settings.AG_SECRET_NAME,
                   key='PASSWORD'
               )
           )),
           client.V1EnvVar(name='STAGING_PASSWORD', value_from=client.V1EnvVarSource(
               secret_key_ref=client.V1SecretKeySelector(
                   name=settings.AG_SECRET_NAME,
                   key='STAGING_PASSWORD'
               )
           ))]

    volume = client.V1Volume(
        name="backupdir",
        persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
            claim_name=settings.AG_PVC_NAME
        )
    )

    container = client.V1Container(
        name=settings.AG_NAME,
        image=settings.AG_IMAGE_NAME,
        image_pull_policy="IfNotPresent",
        command=["/bin/sh", "-c", "/backup/backup.sh"],
        env=ENV,
        volume_mounts=[client.V1VolumeMount(
            mount_path="/backup/dump",
            name="backupdir"
        )],
        resources=client.V1ResourceRequirements(
            requests={"cpu" : settings.AG_CPU_REQUEST, "memory" : settings.AG_MEMORY_REQUEST},
            limits={"cpu" : settings.AG_CPU_LIMIT, "memory" : settings.AG_MEMORY_LIMIT}
        )
    )

    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={
            "snapp.supply/app-name": "aggregation-sync",
            "snapp.supply/app-instance": "aggregation-backup",
            "snapp.supply/app-type": "backup",
            "snapp.supply/app-environment" : settings.AG_NAMESPACE
            }),
        spec=client.V1PodSpec(restart_policy="Never",
                              containers=[container],
                              volumes=[volume])
    )

    try:
        create_job(settings.AG_NAME, settings.AG_NAMESPACE, template)
    except Exception as e:
        logger.error(f"Error occured during creating job: {str(e)}")
        raise HTTPException(status_code=500, detail='Job creation failed.')
    
    return JSONResponse({"Status" : "Created"})



@router.get("/devops-tools/v1/kubernetes/jobs/aggregation/status/")
async def aggregation_job_status(job_name: str):
    status = job_status(job_name, settings.AG_NAMESPACE)
    
    if status not in range(200, 299) and type(status) == int:
        raise HTTPException(status_code=status, detail='Failed to get the job status.')
    
    return JSONResponse(status)

    




