from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from .routers import lock
import os

app = FastAPI()

app.include_router(lock.router)


templates = Jinja2Templates(directory="app/templates")

base_url = os.getenv("BASE_URL")

@app.get("/", response_class=HTMLResponse)
async def form(request: Request):
    locked_time = await lock.locked_days()
    return templates.TemplateResponse(name="index.html", context={
                                        "request": request, 
                                        "locked_time": locked_time, 
                                        "base_url": base_url})
