"""Customer authentication dependencies."""

from typing import Annotated

from fastapi import Header, HTTPException, status

from app.apps.auth.service import customer_auth_service
from app.apps.users.schemas import CustomerProfile
from app.apps.users.service import customer_user_service


async def require_current_customer(
    authorization: Annotated[str | None, Header()] = None,
) -> CustomerProfile:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")

    user_id = customer_auth_service.get_user_id_by_token(authorization.removeprefix("Bearer ").strip())
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")

    user = customer_user_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")
    if user.blacklisted:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被限制使用")
    return user

