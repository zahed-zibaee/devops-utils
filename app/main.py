from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from .routers import lock, product_tax_moadian
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os


app = FastAPI()
security = HTTPBasic()


#app.include_router(lock.router)
app.include_router(product_tax_moadian.router)

