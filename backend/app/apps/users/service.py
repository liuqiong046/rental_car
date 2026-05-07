"""Customer profile service."""

from uuid import uuid4

from fastapi import HTTPException, status

from app.apps.users.schemas import (
    ChannelSource,
    CustomerPhoneUpdateRequest,
    CustomerProfile,
    CustomerProfileUpdateRequest,
)


class CustomerUserService:
    def __init__(self) -> None:
        # TODO(WF-P0-04): 用户资料、渠道来源、手机号变更和黑名单状态需落库，
        # 当前内存数据仅支撑登录/我的页面空跑。
        self.users_by_phone: dict[str, CustomerProfile] = {
            "19898766543": CustomerProfile(
                user_id="user_demo",
                nickname="山海用户",
                avatar_text="山",
                phone_mask=_mask_phone("19898766543"),
                certification_status="unverified",
            ),
            "19900000000": CustomerProfile(
                user_id="user_blacklist",
                nickname="受限用户",
                avatar_text="限",
                phone_mask=_mask_phone("19900000000"),
                certification_status="unverified",
                blacklisted=True,
            ),
        }

    def get_or_create_user(
        self,
        phone: str,
        channel_source: ChannelSource | None,
    ) -> CustomerProfile:
        user = self.users_by_phone.get(phone)
        if user is None:
            user = CustomerProfile(
                user_id=f"user_{uuid4().hex[:8]}",
                nickname="山海用户",
                avatar_text="山",
                phone_mask=_mask_phone(phone),
                certification_status="unverified",
                channel_source=channel_source,
            )
        elif channel_source is not None:
            user = user.model_copy(update={"channel_source": channel_source})
        self.users_by_phone[phone] = user
        return user

    def get_user_by_id(self, user_id: str) -> CustomerProfile | None:
        for user in self.users_by_phone.values():
            if user.user_id == user_id:
                return user
        return None

    def update_profile(
        self,
        user_id: str,
        payload: CustomerProfileUpdateRequest,
    ) -> CustomerProfile:
        user = self.get_user_by_id(user_id)
        if user is None:
            raise ValueError("user not found")
        updated = user.model_copy(
            update={
                key: value
                for key, value in {
                    "nickname": payload.nickname,
                    "avatar_text": payload.avatar_text,
                }.items()
                if value is not None
            },
        )
        self.users_by_phone[_phone_key_by_user(self.users_by_phone, user_id)] = updated
        return updated

    def update_phone(
        self,
        user_id: str,
        payload: CustomerPhoneUpdateRequest,
    ) -> CustomerProfile:
        if payload.verification_code != "1234":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误")
        current_phone = _phone_key_by_user(self.users_by_phone, user_id)
        user = self.users_by_phone.pop(current_phone)
        existing = self.users_by_phone.get(payload.phone)
        if existing is not None and existing.user_id != user_id:
            self.users_by_phone[current_phone] = user
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="手机号已被占用")

        updated = user.model_copy(update={"phone_mask": _mask_phone(payload.phone)})
        self.users_by_phone[payload.phone] = updated
        return updated

    def update_certification_status(self, user_id: str, status: str) -> CustomerProfile:
        user = self.get_user_by_id(user_id)
        if user is None:
            raise ValueError("user not found")
        updated = user.model_copy(update={"certification_status": status})
        self.users_by_phone[_phone_key_by_user(self.users_by_phone, user_id)] = updated
        return updated


def _mask_phone(phone: str) -> str:
    return f"{phone[:3]}****{phone[-4:]}"


def _phone_key_by_user(users_by_phone: dict[str, CustomerProfile], user_id: str) -> str:
    for phone, user in users_by_phone.items():
        if user.user_id == user_id:
            return phone
    raise ValueError("user not found")


customer_user_service = CustomerUserService()
