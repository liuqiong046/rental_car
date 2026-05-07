"""Customer user API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.apps.users.deps import require_current_customer
from app.apps.users.schemas import (
    CustomerPhoneUpdateRequest,
    CustomerProfile,
    CustomerProfileUpdateRequest,
)
from app.apps.users.service import customer_user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=CustomerProfile,
    status_code=status.HTTP_200_OK,
    summary="查询当前 C 端用户资料",
)
async def read_current_user(
    customer: Annotated[CustomerProfile, Depends(require_current_customer)],
) -> CustomerProfile:
    return customer


@router.patch(
    "/me",
    response_model=CustomerProfile,
    status_code=status.HTTP_200_OK,
    summary="更新当前 C 端用户资料",
)
async def update_current_user(
    payload: CustomerProfileUpdateRequest,
    customer: Annotated[CustomerProfile, Depends(require_current_customer)],
) -> CustomerProfile:
    return customer_user_service.update_profile(customer.user_id, payload)


@router.patch(
    "/me/phone",
    response_model=CustomerProfile,
    status_code=status.HTTP_200_OK,
    summary="修改当前 C 端用户手机号",
)
async def update_current_user_phone(
    payload: CustomerPhoneUpdateRequest,
    customer: Annotated[CustomerProfile, Depends(require_current_customer)],
) -> CustomerProfile:
    return customer_user_service.update_phone(customer.user_id, payload)
