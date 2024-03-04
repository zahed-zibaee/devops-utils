from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from .routers import lock


app = FastAPI()

app.include_router(lock.router)


templates = Jinja2Templates(directory="app/templates")

def https_url_for(request: Request, name: str, **path_params) -> str:

    http_url = request.url_for(name, **path_params)

    # Replace 'http' with 'https'
    return http_url.replace("http", "https", 1)

templates.env.globals["https_url_for"] = https_url_for



@app.get("/", response_class=HTMLResponse)
async def form(request: Request):
    locked_time = await lock.locked_days()
    return templates.TemplateResponse(name="index.html", context={"request": request, "locked_time": locked_time})
