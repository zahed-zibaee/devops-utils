from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.redis import RedisClient
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

app.add_event_handler('shutdown', lambda: RedisClient.close_redis())
    
@app.get("/api/v1/healthcheck")
async def get_health():
    """
    ## Perform a Health Check
    Endpoint to perform a healthcheck on. This endpoint can primarily be used Docker
    to ensure a robust container orchestration and management is in place. Other
    services which rely on proper functioning of the API service will not deploy if this
    endpoint returns any other HTTP status code except 200 (OK).
    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return {'status': 'OK'}

app.mount("/devops-tools-front/static", StaticFiles(directory="app/statics"), name="static")

for feature in get_active_features():
    app.include_router(feature.router)
