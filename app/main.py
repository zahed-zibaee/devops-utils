from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
#from fastapi.security import HTTPBasic

from app.core.config import settings
from app.routers import lock, product_tax_moadian, prometheus
from app.core.middleware import LoggingMiddleware

#security = HTTPBasic()

def get_application():
    _app = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG
        )

    return _app

app = get_application()
#app.middleware('http')(
#    LoggingMiddleware()
#)

#app.include_router(lock.router)
app.mount("/devops-tools-front/static", StaticFiles(directory="app/statics"), name="static")
app.include_router(product_tax_moadian.router)
app.include_router(prometheus.router)