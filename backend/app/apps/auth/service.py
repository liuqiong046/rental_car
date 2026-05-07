"""Customer auth service."""

from uuid import uuid4

from fastapi import HTTPException, status

from app.apps.auth.schemas import CustomerLoginRequest, CustomerLoginResponse, SmsCodeRequest
from app.apps.users.service import customer_user_service


class CustomerAuthService:
    def __init__(self) -> None:
        # TODO(WF-P0-04): 接入微信手机号授权/短信供应商，并将 token、openid/unionid
        # 与验证码状态持久化。
        self.tokens: dict[str, str] = {}
        self.verification_codes: dict[str, str] = {}

    def send_sms_code(self, payload: SmsCodeRequest) -> None:
        self.verification_codes[payload.phone] = "1234"

    def login(self, payload: CustomerLoginRequest) -> CustomerLoginResponse:
        expected_code = self.verification_codes.get(payload.phone, "1234")
        if payload.verification_code != expected_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误")

        user = customer_user_service.get_or_create_user(payload.phone, payload.channel_source)
        if user.blacklisted:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被限制使用")

        token = f"usr_{uuid4().hex}"
        self.tokens[token] = user.user_id
        return CustomerLoginResponse(access_token=token, user=user)

    def get_user_id_by_token(self, token: str) -> str | None:
        return self.tokens.get(token)

    def logout(self, user_id: str) -> None:
        expired_tokens = [token for token, stored_id in self.tokens.items() if stored_id == user_id]
        for token in expired_tokens:
            self.tokens.pop(token, None)


customer_auth_service = CustomerAuthService()
