from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/devops-tools-front/v1/component/products/tax_and_moadian")
async def get_products_component(request: Request):
    return templates.TemplateResponse("components/product_tax_and_moadian_id_list/index.html", {
        "request": request, 
        "title": "Products", 
        "description": "Product list/import for tax rate and moadian samane ID.",
        })

@router.get("/devops-tools-front/v1/component/app_settings")
async def get_products_component(request: Request):
    return templates.TemplateResponse("components/app-settings/index.html", {
        "request": request, 
        "title": "App Settings", 
        "description": "Check and edit app settings.",
        })
