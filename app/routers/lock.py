from fastapi import Body, status, Response, APIRouter
import ast
from gitlab import Gitlab
import re
import os
from .argocd import refresh_app



GITLAB_URL = os.getenv("GITLAB_URL")
GITLAB_ACCESS_TOKEN = os.getenv("GITLAB_ACCESS_TOKEN")
ORDER_FILE_PATH = os.getenv("ORDER_FILE_PATH")
LEGACY_FILE_PATH = os.getenv("LEGACY_FILE_PATH")
GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID")
COMMIT_MESSAGE = os.getenv("COMMIT_MESSAGE")


router = APIRouter()



def receive_gitlab_data():
    gitlab = Gitlab(f"{GITLAB_URL}", private_token=f"{GITLAB_ACCESS_TOKEN}")
    project = gitlab.projects.get(int(GITLAB_PROJECT_ID))
    return project



@router.post("/lock")
async def receive_days(response: Response, input: str = Body(...)):
 
    project = receive_gitlab_data()

    print(f"Changing order service lock time to: {input}")
    number = ast.literal_eval(input)["text"]

    try:
        order = project.files.get(file_path=f'{ORDER_FILE_PATH}', ref='main')
        data = order.decode()
        new_order_content = re.sub(rb'(?m)^  - name: VALID_((?:BASKET|ORDER))_UPDATE_TIME_IN_DAYS\n    value: "(\d+)"\n', rf'  - name: VALID_\1_UPDATE_TIME_IN_DAYS\n    value: "{number}"\n'.encode(), data)

        new_order_content = str(new_order_content, encoding="utf-8")
        order.content = new_order_content
        order.save(branch="main", commit_message=f'{COMMIT_MESSAGE}')

        legacy = project.files.get(file_path=f"{LEGACY_FILE_PATH}", ref='main')
        data = legacy.decode()
        new_legacy_content = re.sub(rb'(?m)^  - name: VALID_ORDER_UPDATE_TIME_IN_DAYS\n    value: (\d+)\n', rf'  - name: VALID_ORDER_UPDATE_TIME_IN_DAYS\n    value: {number}\n'.encode(), data)

        new_legacy_content = str(new_legacy_content, encoding="utf-8")
        legacy.content = new_legacy_content
        legacy.save(branch="main", commit_message=f'{COMMIT_MESSAGE}')
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise e
    
    try:
        refresh_app()
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise e
    

    
    
    response.status_code = status.HTTP_200_OK
    return response


async def locked_days():
    project = receive_gitlab_data()

    order = project.files.get(file_path=f'{ORDER_FILE_PATH}', ref='main')
    data = order.decode()
    match_order = re.search(rb'(?m)^  - name: VALID_ORDER_UPDATE_TIME_IN_DAYS\n    value: "(\d+)"\n', data)

    
    legacy = project.files.get(file_path=f"{LEGACY_FILE_PATH}", ref='main')
    data = legacy.decode()
    match_legacy = re.search(rb'(?m)^  - name: VALID_ORDER_UPDATE_TIME_IN_DAYS\n    value: (\d+)\n', data)

    if match_order and match_legacy:
        value = match_legacy.group(1)
        return int(value.decode())
    else:
        print("Value not found")
        