from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.feature_status import feature_status


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/devops-tools-front/v1/component/products/tax_and_moadian")
async def get_products_component(request: Request):
    return templates.TemplateResponse("components/product_tax_and_moadian_id_list/index.html", {
        "request": request, 
        "title": "Products", 
        "hash": settings.GIT_HASH,
        "description": "Product list/import for tax rate and moadian samane ID.",
        "disabled_feature": {
            "product_tax_moadian": feature_status('product_tax_moadian')
        }, 
        })

@router.get("/devops-tools-front/v1/component/app_settings")
async def get_app_settings_component(request: Request):
    return templates.TemplateResponse("components/app-settings/index.html", {
        "request": request, 
        "title": "App Settings", 
        "hash": settings.GIT_HASH,
        "description": "Check and edit app settings.",
        "disabled_feature": {
            "order_lock": feature_status('order_lock'),
            "aggregation": feature_status('aggregation'),
            "access_management": feature_status('access_management'),
        },
        })

@router.get("/devops-tools-front/v1/component/monitor")
async def get_monitoring_component(request: Request):
    return templates.TemplateResponse("components/monitoring/index.html", {
        "request": request, 
        "title": "Monitoring", 
        "hash": settings.GIT_HASH,
        "description": "Monitor Service Statuses",
        "disabled_feature": {
            "kafka_lag_consumer_group": feature_status('kafka_lag_consumer_group'),
        },
        })