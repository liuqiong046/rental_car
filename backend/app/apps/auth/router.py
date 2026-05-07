"""Customer auth API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.apps.auth.schemas import CustomerLoginRequest, CustomerLoginResponse, SmsCodeRequest
from app.apps.auth.service import customer_auth_service
from app.apps.users.deps import require_current_customer
from app.apps.users.schemas import CustomerProfile

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/sms-code",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="发送 C 端手机号验证码",
)
async def send_sms_code(payload: SmsCodeRequest) -> None:
    customer_auth_service.send_sms_code(payload)


@router.post(
    "/phone-login",
    response_model=CustomerLoginResponse,
    status_code=status.HTTP_200_OK,
    summary="C 端手机号登录",
)
async def phone_login(payload: CustomerLoginRequest) -> CustomerLoginResponse:
    return customer_auth_service.login(payload)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="C 端退出登录",
)
async def logout(customer: Annotated[CustomerProfile, Depends(require_current_customer)]) -> None:
    customer_auth_service.logout(customer.user_id)
