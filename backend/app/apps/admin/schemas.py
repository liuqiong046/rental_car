"""Pydantic DTOs for PC admin auth and RBAC."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AdminRoleCode = Literal["hq_admin", "ops_admin", "dealer_admin", "finance", "support", "dispatcher"]
AccountStatus = Literal["active", "disabled", "locked"]
DataScopeType = Literal["all", "city", "organization"]
OrganizationType = Literal["headquarters", "operation_center", "dealer", "department", "position"]


class DataScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: DataScopeType
    city_code: str | None = None
    organization_id: str | None = None


class AdminRole(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    code: AdminRoleCode
    name: str
    menus: list[str]
    buttons: list[str]
    data_scope: DataScope


class Organization(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    type: OrganizationType
    parent_id: str | None = None
    city_code: str | None = None
    status: AccountStatus = "active"


class AdminActor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    username: str
    display_name: str
    organization: Organization
    role: AdminRole
    status: AccountStatus


class AdminLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=6, max_length=64)


class AdminLoginResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    actor: AdminActor


class OrganizationListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[Organization]
    total: int


class RoleListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AdminRole]
    total: int


class AccountListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AdminActor]
    total: int


class AccountCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=2, max_length=32)
    display_name: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=6, max_length=64)
    organization_id: str
    role_id: str


class OrganizationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=32)
    type: OrganizationType
    parent_id: str | None = None
    city_code: str | None = Field(default=None, max_length=12)


class OrganizationUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=32)
    parent_id: str | None = None
    city_code: str | None = Field(default=None, max_length=12)
    status: AccountStatus | None = None


class RoleCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: AdminRoleCode
    name: str = Field(min_length=2, max_length=32)
    menus: list[str] = Field(default_factory=list, max_length=50)
    buttons: list[str] = Field(default_factory=list, max_length=80)
    data_scope: DataScope


class RoleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=32)
    menus: list[str] | None = Field(default=None, max_length=50)
    buttons: list[str] | None = Field(default=None, max_length=80)
    data_scope: DataScope | None = None


class AccountUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=2, max_length=32)
    organization_id: str | None = None
    role_id: str | None = None


class AccountStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: AccountStatus


class AccountPasswordResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: str = Field(min_length=6, max_length=64)
