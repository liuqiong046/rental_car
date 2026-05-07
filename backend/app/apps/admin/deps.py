"""Admin authentication and authorization dependencies."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.apps.admin.schemas import AdminActor, AdminRoleCode
from app.apps.admin.service import admin_service


async def require_admin_actor(
    authorization: Annotated[str | None, Header()] = None,
) -> AdminActor:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")

    token = authorization.removeprefix("Bearer ").strip()
    actor = admin_service.get_actor_by_token(token)
    if actor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")
    if actor.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号不可用")
    return actor


def require_role(*roles: AdminRoleCode):
    async def dependency(actor: Annotated[AdminActor, Depends(require_admin_actor)]) -> AdminActor:
        if actor.role.code not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
        return actor

    return dependency

