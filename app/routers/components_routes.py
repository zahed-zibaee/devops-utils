from fastapi import APIRouter

from app.core.feature_status import feature_status


router = APIRouter()

@router.get("/devops-tools/v1/component/routes")
async def get_tools():
    tools = []
    if feature_status('product_tax_moadian'):
        tools.append({
            "name": "مالیات و کد کالا",
            "endpoint": "/products/tax_and_moadian",
        })
    if feature_status('app_settings'):
        tools.append({
            "name": "تنظيمات برنامه",
            "endpoint": "app_settings",
        })
    if feature_status('monitoring'):
        tools.append({
            "name": "نظارت",
            "endpoint": "monitor",
        })
    return tools
