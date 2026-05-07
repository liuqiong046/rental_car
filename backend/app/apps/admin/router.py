"""Admin API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.apps.admin.deps import require_admin_actor
from app.apps.admin.schemas import (
    AccountCreateRequest,
    AccountListResponse,
    AccountPasswordResetRequest,
    AccountStatusUpdateRequest,
    AccountUpdateRequest,
    AdminActor,
    AdminLoginRequest,
    AdminLoginResponse,
    Organization,
    OrganizationCreateRequest,
    OrganizationListResponse,
    OrganizationUpdateRequest,
    RoleCreateRequest,
    RoleListResponse,
    RoleUpdateRequest,
    AdminRole,
)
from app.apps.admin.service import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/auth/login",
    response_model=AdminLoginResponse,
    status_code=status.HTTP_200_OK,
    summary="PC 后台账号登录",
)
async def login(payload: AdminLoginRequest) -> AdminLoginResponse:
    return admin_service.login(payload)


@router.get(
    "/auth/me",
    response_model=AdminActor,
    status_code=status.HTTP_200_OK,
    summary="查询当前后台账号",
)
async def read_current_admin(
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> AdminActor:
    return actor


@router.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="退出 PC 后台登录",
)
async def logout(actor: Annotated[AdminActor, Depends(require_admin_actor)]) -> None:
    admin_service.logout(actor.account_id)


@router.get(
    "/organizations",
    response_model=OrganizationListResponse,
    status_code=status.HTTP_200_OK,
    summary="查询组织列表",
)
async def list_organizations(
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> OrganizationListResponse:
    return admin_service.list_organizations(actor)


@router.post(
    "/organizations",
    response_model=Organization,
    status_code=status.HTTP_201_CREATED,
    summary="新增后台组织",
)
async def create_organization(
    payload: OrganizationCreateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> Organization:
    return admin_service.create_organization(actor, payload)


@router.patch(
    "/organizations/{organization_id}",
    response_model=Organization,
    status_code=status.HTTP_200_OK,
    summary="更新后台组织",
)
async def update_organization(
    organization_id: str,
    payload: OrganizationUpdateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> Organization:
    return admin_service.update_organization(actor, organization_id, payload)


@router.get(
    "/roles",
    response_model=RoleListResponse,
    status_code=status.HTTP_200_OK,
    summary="查询角色列表",
)
async def list_roles(
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> RoleListResponse:
    return admin_service.list_roles(actor)


@router.post(
    "/roles",
    response_model=AdminRole,
    status_code=status.HTTP_201_CREATED,
    summary="新增后台角色",
)
async def create_role(
    payload: RoleCreateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> AdminRole:
    return admin_service.create_role(actor, payload)


@router.patch(
    "/roles/{role_id}",
    response_model=AdminRole,
    status_code=status.HTTP_200_OK,
    summary="更新后台角色",
)
async def update_role(
    role_id: str,
    payload: RoleUpdateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> AdminRole:
    return admin_service.update_role(actor, role_id, payload)


@router.get(
    "/accounts",
    response_model=AccountListResponse,
    status_code=status.HTTP_200_OK,
    summary="查询后台账号列表",
)
async def list_accounts(
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> AccountListResponse:
    return admin_service.list_accounts(actor)


@router.post(
    "/accounts",
    response_model=AdminActor,
    status_code=status.HTTP_201_CREATED,
    summary="新增后台账号",
)
async def create_account(
    payload: AccountCreateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> AdminActor:
    return admin_service.create_account(actor, payload)


@router.patch(
    "/accounts/{account_id}",
    response_model=AdminActor,
    status_code=status.HTTP_200_OK,
    summary="编辑后台账号",
)
async def update_account(
    account_id: str,
    payload: AccountUpdateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> AdminActor:
    return admin_service.update_account(actor, account_id, payload)


@router.patch(
    "/accounts/{account_id}/status",
    response_model=AdminActor,
    status_code=status.HTTP_200_OK,
    summary="更新后台账号状态",
)
async def update_account_status(
    account_id: str,
    payload: AccountStatusUpdateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> AdminActor:
    return admin_service.update_account_status(actor, account_id, payload.status)


@router.post(
    "/accounts/{account_id}/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="重置后台账号密码",
)
async def reset_account_password(
    account_id: str,
    payload: AccountPasswordResetRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> None:
    admin_service.reset_account_password(actor, account_id, payload.password)
