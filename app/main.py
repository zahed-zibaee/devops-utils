from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from .routers import lock
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os


app = FastAPI()
security = HTTPBasic()


app.include_router(lock.router)


templates = Jinja2Templates(directory="app/templates")

BASE_URL = os.getenv("BASE_URL")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD")
AUTH_USERNAME = os.getenv("AUTH_USERNAME")



async def requires_auth(credentials: HTTPBasicCredentials = Depends(security)):

    if credentials.username != AUTH_USERNAME or credentials.password != AUTH_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )


@app.get("/", response_class=HTMLResponse)
async def form(request: Request, credentials: HTTPBasicCredentials = Depends(requires_auth)):
    locked_time = await lock.locked_days()
    return templates.TemplateResponse(name="index.html", context={
                                        "request": request, 
                                        "locked_time": locked_time, 
                                        "base_url": BASE_URL})
