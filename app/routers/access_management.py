from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi_pagination import add_pagination, Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.exc import IntegrityError
from sqlalchemy import String

from app.core.db import get_db_postgres_access_read, get_db_postgres_access_write
from app.schemas.main import Access, Permissions, PermissionsBase, PermissionsUpdate, AccessBase, AccessUpdate, PermissionLabels

router = APIRouter()


@router.get("/devops-tools/v1/access/endpoint/list", response_model=Page[AccessUpdate])
async def list_access(
    db: AsyncSession = Depends(get_db_postgres_access_read),
    search: str = Query(None, description="Search term to filter access by slug or path")
    ):

    query = select(Access)
    if search:
        query = query.where(
            (Access.slug.ilike(f"%{search}%")) |
            (Access.path.ilike(f"%{search}%")) |
            (Access.id.cast(String).ilike(f"%{search}%"))

        )

    return paginate(db, query)

add_pagination(router)

@router.post("/devops-tools/v1/access/endpoint/create", response_model=AccessBase)
async def create_access_rule(access: AccessBase, db: AsyncSession = Depends(get_db_postgres_access_write)):
    new_access_rule = Access(
        slug=access.slug,
        path=access.path,
        method=access.method,
        permission_ids=access.permission_ids,
        public=access.public
    )
    
    db.add(new_access_rule)

    try:
        db.commit()
        db.refresh(new_access_rule)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Rule could not be created")

    return new_access_rule

@router.put("/devops-tools/v1/access/endpoint/update/{rule_id}", response_model=AccessBase)
async def update_item(rule_id: int, rule_update: AccessUpdate, db: AsyncSession = Depends(get_db_postgres_access_write)):

    result = db.execute(select(Access).where(Access.id == rule_id))
    rule = result.scalars().first()

    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule.slug = set_if_not_none(rule_update.slug, rule.slug)
    rule.path = set_if_not_none(rule_update.path, rule.path)
    rule.permission_ids = set_if_not_none(rule_update.permission_ids, rule.permission_ids)
    rule.method = set_if_not_none(rule_update.method, rule.method)
    rule.public = set_if_not_none(rule_update.public, rule.public)

    if rule_update.slug is not None:
        rule.slug

    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/devops-tools/v1/access/endpoint/{rule_id}", response_model=AccessBase)
async def delete_item(rule_id: int, db: AsyncSession = Depends(get_db_postgres_access_write)):
    result = db.execute(select(Access).where(Access.id == rule_id))
    rule = result.scalars().first()

    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()

    return rule

# Permissions Table

@router.get("/devops-tools/v1/access/permissions/list", response_model=Page[PermissionsUpdate])
async def list_permissions(
    db: AsyncSession = Depends(get_db_postgres_access_read),
    search: str = Query(None, description="Search term to filter access by slug or path")
    ):

    query = select(Permissions)
    if search:
        query = query.where(
            (Permissions.slug.ilike(f"%{search}%")) |
            (Permissions.label.ilike(f"%{search}%")) |
            (Permissions.id.cast(String).ilike(f"%{search}%"))

        )

    return paginate(db, query)

add_pagination(router)

@router.post("/devops-tools/v1/access/permissions/create", response_model=PermissionsBase)
async def create_permission(permission: PermissionsBase, db: AsyncSession = Depends(get_db_postgres_access_write)):
    new_permission = Permissions(
        slug=permission.slug,
        label=permission.label
    )
    
    db.add(new_permission)

    try:
        db.commit()
        db.refresh(new_permission)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Permission could not be created")

    return new_permission

@router.put("/devops-tools/v1/access/permissions/update/{permission_id}", response_model=PermissionsBase)
async def update_permission(permission_id: int, permission_update:PermissionsUpdate , db: AsyncSession = Depends(get_db_postgres_access_write)):

    result = db.execute(select(Permissions).where(Permissions.id == permission_id))
    permission = result.scalars().first()

    if permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")

    permission.slug = set_if_not_none(permission_update.slug, permission.slug)
    permission.label = set_if_not_none(permission_update.label, permission.label)

    if permission_update.slug is not None:
        permission.slug

    db.commit()
    db.refresh(permission)
    return permission

@router.delete("/devops-tools/v1/access/permissions/{permission_id}", response_model=PermissionsBase)
async def delete_item(permission_id: int, db: AsyncSession = Depends(get_db_postgres_access_write)):
    result = db.execute(select(Permissions).where(Permissions.id == permission_id))
    permission = result.scalars().first()

    if permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")

    db.delete(permission)
    db.commit()

    return permission

@router.get("/devops-tools/v1/access/permissions/{permission_id}", response_model=str)
async def get_permission_label(permission_id: int, db: AsyncSession = Depends(get_db_postgres_access_read)):
    result = db.execute(select(Permissions).where(Permissions.id == permission_id))
    permission = result.scalars().first()

    if permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")

    return permission.label

def set_if_not_none(src, dst):
    if src is not None:
        dst = src

    return dst