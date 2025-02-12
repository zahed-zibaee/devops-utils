from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from gitlab import Gitlab
import re

from app.core.config import settings
from app.core.redis import get_cache, set_cache
from app.core.argocd import refresh_app
from app.core.logging import logger
from app.schemas.order_lock import EditOrderLock
from app.core.redis import lock, unlock, is_locked


router = APIRouter()

def receive_gitlab_manifest_data():
    try:
        gitlab = Gitlab(f"{settings.GITLAB_URL}", private_token=f"{settings.GITLAB_ACCESS_TOKEN_MANIFEST}")
        project = gitlab.projects.get(settings.GITLAB_PROJECT_ID_MANIFEST)
        return project
    except Exception as e:
        logger.error(f"Can not get manifest project gitlab data. error: {str(e)}")
        raise HTTPException(status_code=503, detail='Can not get manifest project gitlab data.')

def get_gitlab_file_content_lock(project_name ,manifest_project ,file_path):
    try:
        file = manifest_project.files.get(file_path=f'{file_path}', ref='main')
        return file
    except Exception as e:
        logger.error(f"Can not generate {project_name} manifest file data. error: {str(e)}")
        raise HTTPException(status_code=503, detail=f'Can not generate {project_name} manifest file data.')
    
@router.put("/devops-tools/v1/order/lock/edit")
async def order_lock_edit(params: EditOrderLock):
    manifest_project = receive_gitlab_manifest_data() 
    try:
        order_file = get_gitlab_file_content_lock('order', manifest_project, settings.ORDER_FILE_PATH_MANIFEST)
    except Exception as e:
        logger.error(f"Can not get manifest files. error: {str(e)}")
        raise HTTPException(status_code=503, detail='Can not get manifest files.')
    try:
        order_file_decoded = order_file.decode()
    except Exception as e:
        logger.error(f"Can not decode manifest files. error: {str(e)}")
        raise HTTPException(status_code=503, detail='Can not decode manifest files.')
    new_order_content = re.sub(
        rb'(?m)^  - name: VALID_((?:BASKET|ORDER))_UPDATE_TIME_IN_DAYS\n    value: "(\d+)"\n', rf'  - name: VALID_\1_UPDATE_TIME_IN_DAYS\n    value: "{params.lock}"\n'.encode(), 
        order_file_decoded
    )
    order_file.content = str(new_order_content, encoding="utf-8")
    set_cache("lock", "order_lock", params.lock, 86400)
    logger.info("acquiring lock for git manifest project.")
    logger.info(is_locked('GIT_MANIFEST_PROJECT'))
    if not is_locked("GIT_MANIFEST_PROJECT"):
        try:
            lock("GIT_MANIFEST_PROJECT", 60)
            logger.info(is_locked('GIT_MANIFEST_PROJECT'))
            order_file.save(branch="main", commit_message=settings.COMMIT_MESSAGE_CHANGE_ORDER_LOCK)
        except Exception as e:
            logger.error(f"Can not save manifest files. error: {str(e)}")
            raise HTTPException(status_code=503, detail='Can not save manifest files.')
        finally:
            unlock("GIT_MANIFEST_PROJECT")
            logger.info(is_locked('GIT_MANIFEST_PROJECT'))
    else:
        raise HTTPException(status_code=409, detail="Operation GIT_MANIFEST_PROJECT is already in progress")
    refresh_app(settings.ORDER_ARGOCD_APP_NAME)
    logger.warning(f"Order lock time changed to {params.lock} days.")
    return JSONResponse(f"Order lock time changed to {params.lock} days.")

@router.get("/devops-tools/v1/order/lock")
async def get_lock_time():
    cached_lock = get_cache("lock", "order_lock")
    if cached_lock:
        return JSONResponse({"lock": cached_lock})
    manifest_project = receive_gitlab_manifest_data()
    match_order_data = re.search(
        rb'(?m)^  - name: VALID_ORDER_UPDATE_TIME_IN_DAYS\n    value: "(\d+)"\n', 
        get_gitlab_file_content_lock('order', manifest_project, settings.ORDER_FILE_PATH_MANIFEST).decode()
    )
    set_cache("lock", "order_lock", match_order_data.group(1).decode(), 86400)
    return JSONResponse({"lock": match_order_data.group(1).decode()})
