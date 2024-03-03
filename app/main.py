from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from .routers import lock


app = FastAPI()
app.add_middleware(HTTPSRedirectMiddleware)

app.include_router(lock.router)


templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def form(request: Request):
    locked_time = await lock.locked_days()
    return templates.TemplateResponse(name="index.html", context={"request": request, "locked_time": locked_time})
