from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.toggle_feature import get_active_features
from app.core.middleware import LoggingMiddleware

def get_application():
    _app = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG
        )

    return _app

app = get_application()
app.middleware('http')(
    LoggingMiddleware()
)

app.mount("/devops-tools-front/static", StaticFiles(directory="app/statics"), name="static")

for feature in get_active_features():
    app.include_router(feature.router)