from fastapi import APIRouter

router = APIRouter()

@router.get("/devops-tools/v1/routes")
async def get_tools():
    return [
        {
            "name": "مالیات و کد کالا",
            "url": "tax_and_moadian"
        },
    ]