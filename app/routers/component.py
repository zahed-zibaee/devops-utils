from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.feature_flag import feature_status


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/devops-tools-front/v1/component/products/tax_and_moadian")
async def get_products_tax_and_moadian_component(request: Request):
    return templates.TemplateResponse(
        "components/data/view-table1.html", 
        {
            "request": request, 
            "title": "Products Rax And Moadian ID", 
            "hash": settings.GIT_HASH,
            "description": "Product list/import/edit for tax rate and moadian samane ID.<br><div class='note'>note: import csv only applies data update.</div>",
            "disabled_feature": {
                "product_tax_moadian": feature_status('product_tax_moadian')
            },
            "show_add_button": False,
            "show_export_button": True,
            "show_import_button": True,
            "show_delete_button": False,
            "show_sync_button": False,
            "show_edit_button": True,
            "list_func": "ajaxRequestProductTaxMoadian",
            "export_url": "/devops-tools/v1/products/tax_and_moadian/export_csv",
            "import_url": "/devops-tools/v1/products/tax_and_moadian/import_csv/",
            "import_status_url": "/devops-tools/v1/products/tax_and_moadian/import_csv/status/",
            "save_edit_function": "ajaxEditProductTaxAndMoadian",
            "delete_url": "/devops-tools/v1/products/tax_and_moadian/",
            "add_url": "/devops-tools/v1/products/tax_and_moadian",
            "table_columns": [
                {"field": "id", "title": "ID", "sortable": True},
                {"field": "name", "title": "Name"},
                {"field": "tax_rate", "title": "Tax Rate", "sortable": True},
                {"field": "moadian_product_id", "title": "Moadian Product ID", "sortable": True},
                {"field": "state", "title": "State", "sortable": True},
                {"field": "actions", "title": "Actions"}
            ],
            "modal_title": "Products Tax and Moadian product ID",
            "modal_fields": [
                {"id": "editID", "label": "ID", "field_key": "id", "readonly": True},
                {"id": "editName", "label": "Name", "field_key": "name", "readonly": True},
                {"id": "editTaxRate", "label": "Tax Rate", "field_key": "tax_rate", "transform": "removeRateFormat"},
                {"id": "editMoadianProductId", "label": "Moadian Product ID", "field_key": "moadian_product_id"}
            ],
            }
        )

@router.get("/devops-tools-front/v1/component/products/products_daily_purchased")
async def get_products_daily_purchased_component(request: Request):
    return templates.TemplateResponse(
        "components/data/view-table1.html", 
        {
            "request": request, 
            "title": "Products Daily Purchased", 
            "hash": settings.GIT_HASH,
            "description": "Products daily purchased list/import/add/edit/delete.<br><div class='note'>note: import csv only applies data update and data insert.</div>",
            "disabled_feature": {
                "products_daily_purchased": feature_status('products_daily_purchased')
            },
            "show_add_button": True,
            "show_export_button": True,
            "show_import_button": True,
            "show_delete_button": True,
            "show_sync_button": False,
            "show_edit_button": True,
            "list_func": "ajaxRequestProductsDailyPurchased",
            "export_url": "/devops-tools/v1/products/products_daily_purchased/export_csv",
            "import_url": "/devops-tools/v1/products/products_daily_purchased/import_csv/",
            "import_status_url": "/devops-tools/v1/products/products_daily_purchased/import_csv/status/",
            "save_edit_function": "ajaxEditProductsDailyPurchased",
            "delete_url": "/devops-tools/v1/products/products_daily_purchased/",
            "add_url": "/devops-tools/v1/products/products_daily_purchased",
            "table_columns": [
                {"field": "id", "title": "ID", "sortable": True},
                {"field": "product_id", "title": "Product ID", "sortable": True},
                {"field": "product_name", "title": "Product Name"},
                {"field": "count", "title": "Count", "sortable": True},
                {"field": "price", "title": "Price", "sortable": True},
                {"field": "description", "title": "Description"},
                {"field": "actions", "title": "Actions"},
            ],
            "modal_title": "Products Daily Purchased",
            "modal_fields": [
                {"id": "editID", "label": "ID", "field_key": "id", "readonly": True},
                {"id": "editProductID", "label": "Product ID", "field_key": "product_id"},
                {"id": "editProductName", "label": "Product Name", "field_key": "product_name" ,"readonly": True},
                {"id": "editDate", "label": "Date", "field_key": "date"},
                {"id": "editCount", "label": "Count", "field_key": "count"},
                {"id": "editPrice", "label": "Price", "field_key": "price", "transform": "removeMoneyFormat"},
                {"id": "editDescription", "label": "Description", "field_key": "description"}
            ],
            }
        )
    
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