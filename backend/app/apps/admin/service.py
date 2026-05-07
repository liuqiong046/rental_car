"""In-memory admin auth and RBAC service for the P0 baseline."""

from hashlib import sha256
from uuid import uuid4

from fastapi import HTTPException, status

from app.apps.admin.schemas import (
    AccountStatus,
    AccountCreateRequest,
    AccountUpdateRequest,
    AdminActor,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminRole,
    DataScope,
    Organization,
    OrganizationCreateRequest,
    OrganizationUpdateRequest,
    RoleCreateRequest,
    RoleUpdateRequest,
)


class AdminService:
    def __init__(self) -> None:
        # TODO(WF-P0-03): 替换内存账号/组织/角色、token 和密码哈希，接入持久化数据源。
        self.organizations = _seed_organizations()
        self.roles = _seed_roles()
        self.accounts = _seed_accounts(self.organizations, self.roles)
        self.password_hashes = {username: _password_hash(username) for username in self.accounts}
        self.tokens: dict[str, str] = {}

    def login(self, payload: AdminLoginRequest) -> AdminLoginResponse:
        actor = self.accounts.get(payload.username)
        if actor is None or _hash_password(payload.password) != self.password_hashes.get(payload.username):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")
        if actor.status != "active" or actor.organization.status != "active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号不可用")

        token = f"adm_{uuid4().hex}"
        self.tokens[token] = actor.account_id
        return AdminLoginResponse(access_token=token, actor=actor)

    def logout(self, account_id: str) -> None:
        expired_tokens = [token for token, stored_id in self.tokens.items() if stored_id == account_id]
        for token in expired_tokens:
            self.tokens.pop(token, None)

    def get_actor_by_token(self, token: str) -> AdminActor | None:
        account_id = self.tokens.get(token)
        if account_id is None:
            return None
        return self._get_actor_by_account_id(account_id)

    def list_organizations(self, actor: AdminActor):
        items = [org for org in self.organizations.values() if _is_org_visible(actor, org)]
        return {"items": items, "total": len(items)}

    def list_roles(self, actor: AdminActor):
        items = [role for role in self.roles.values() if _is_role_visible(actor, role)]
        return {"items": items, "total": len(items)}

    def list_accounts(self, actor: AdminActor):
        items = [account for account in self.accounts.values() if _is_account_visible(actor, account)]
        return {"items": items, "total": len(items)}

    def create_organization(
        self,
        actor: AdminActor,
        payload: OrganizationCreateRequest,
    ) -> Organization:
        if actor.role.data_scope.type != "all":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
        if payload.parent_id and payload.parent_id not in self.organizations:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="上级组织不存在")

        organization = Organization(
            id=f"org_{uuid4().hex[:8]}",
            name=payload.name,
            type=payload.type,
            parent_id=payload.parent_id,
            city_code=payload.city_code,
            status="active",
        )
        self.organizations[organization.id] = organization
        return organization

    def update_organization(
        self,
        actor: AdminActor,
        organization_id: str,
        payload: OrganizationUpdateRequest,
    ) -> Organization:
        organization = self.organizations.get(organization_id)
        if organization is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="组织不存在")
        if actor.role.data_scope.type != "all" and not _is_org_visible(actor, organization):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
        if payload.parent_id and payload.parent_id not in self.organizations:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="上级组织不存在")

        updated = organization.model_copy(
            update={
                key: value
                for key, value in {
                    "name": payload.name,
                    "parent_id": payload.parent_id,
                    "city_code": payload.city_code,
                    "status": payload.status,
                }.items()
                if value is not None
            },
        )
        self.organizations[organization_id] = updated
        self._refresh_account_organizations(updated)
        if updated.status != "active":
            self._logout_accounts_in_organization(updated.id)
        return updated

    def create_role(self, actor: AdminActor, payload: RoleCreateRequest) -> AdminRole:
        role = AdminRole(
            id=f"role_{uuid4().hex[:8]}",
            code=payload.code,
            name=payload.name,
            menus=payload.menus,
            buttons=payload.buttons,
            data_scope=payload.data_scope,
        )
        self._ensure_role_manageable(actor, role)
        self.roles[role.id] = role
        return role

    def update_role(
        self,
        actor: AdminActor,
        role_id: str,
        payload: RoleUpdateRequest,
    ) -> AdminRole:
        role = self.roles.get(role_id)
        if role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
        updated = role.model_copy(
            update={
                key: value
                for key, value in {
                    "name": payload.name,
                    "menus": payload.menus,
                    "buttons": payload.buttons,
                    "data_scope": payload.data_scope,
                }.items()
                if value is not None
            },
        )
        self._ensure_role_manageable(actor, updated)
        self.roles[role_id] = updated
        self._refresh_account_roles(updated)
        return updated

    def create_account(self, actor: AdminActor, payload: AccountCreateRequest) -> AdminActor:
        if payload.username in self.accounts:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="账号已存在")
        org = self.organizations.get(payload.organization_id)
        role = self.roles.get(payload.role_id)
        if org is None or role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="组织或角色不存在")
        if not _is_org_visible(actor, org) or not _is_role_visible(actor, role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

        account = AdminActor(
            account_id=f"acct_{uuid4().hex[:8]}",
            username=payload.username,
            display_name=payload.display_name,
            organization=org,
            role=role,
            status="active",
        )
        self.accounts[payload.username] = account
        self.password_hashes[payload.username] = _hash_password(payload.password)
        return account

    def update_account(
        self,
        actor: AdminActor,
        account_id: str,
        payload: AccountUpdateRequest,
    ) -> AdminActor:
        target = self._get_actor_by_account_id(account_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账号不存在")
        if not _is_account_visible(actor, target):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

        org = target.organization
        role = target.role
        if payload.organization_id is not None:
            org = self.organizations.get(payload.organization_id)
            if org is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="组织不存在")
            if not _is_org_visible(actor, org):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
        if payload.role_id is not None:
            role = self.roles.get(payload.role_id)
            if role is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
            if not _is_role_visible(actor, role):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

        updated = target.model_copy(
            update={
                key: value
                for key, value in {
                    "display_name": payload.display_name,
                    "organization": org,
                    "role": role,
                }.items()
                if value is not None
            },
        )
        self.accounts[updated.username] = updated
        return updated

    def update_account_status(
        self,
        actor: AdminActor,
        account_id: str,
        next_status: AccountStatus,
    ) -> AdminActor:
        target = self._get_actor_by_account_id(account_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账号不存在")
        if not _is_account_visible(actor, target):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

        updated = target.model_copy(update={"status": next_status})
        self.accounts[updated.username] = updated
        if next_status != "active":
            self.logout(updated.account_id)
        return updated

    def reset_account_password(self, actor: AdminActor, account_id: str, password: str) -> None:
        target = self._get_actor_by_account_id(account_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账号不存在")
        if not _is_account_visible(actor, target):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
        self.password_hashes[target.username] = _hash_password(password)
        self.logout(target.account_id)

    def _get_actor_by_account_id(self, account_id: str) -> AdminActor | None:
        for account in self.accounts.values():
            if account.account_id == account_id:
                return account
        return None

    def _ensure_role_manageable(self, actor: AdminActor, role: AdminRole) -> None:
        if not _is_role_visible(actor, role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
        scope = role.data_scope
        if scope.type == "city" and scope.city_code is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="城市数据范围缺少城市")
        if scope.type == "organization" and scope.organization_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="组织数据范围缺少组织")
        if scope.organization_id and scope.organization_id not in self.organizations:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="组织不存在")

    def _refresh_account_organizations(self, organization: Organization) -> None:
        self.accounts = {
            username: account.model_copy(update={"organization": organization})
            if account.organization.id == organization.id
            else account
            for username, account in self.accounts.items()
        }

    def _refresh_account_roles(self, role: AdminRole) -> None:
        self.accounts = {
            username: account.model_copy(update={"role": role})
            if account.role.id == role.id
            else account
            for username, account in self.accounts.items()
        }

    def _logout_accounts_in_organization(self, organization_id: str) -> None:
        account_ids = [
            account.account_id
            for account in self.accounts.values()
            if account.organization.id == organization_id
        ]
        for account_id in account_ids:
            self.logout(account_id)


def _seed_organizations() -> dict[str, Organization]:
    organizations = [
        Organization(id="org_hq", name="山海总部", type="headquarters"),
        Organization(id="org_sanya", name="三亚运营中心", type="operation_center", city_code="SY"),
        Organization(id="org_dealer_a", name="海棠湾车行", type="dealer", parent_id="org_sanya", city_code="SY"),
    ]
    return {org.id: org for org in organizations}


def _seed_roles() -> dict[str, AdminRole]:
    roles = [
        AdminRole(
            id="role_hq_admin",
            code="hq_admin",
            name="总部管理员",
            menus=["dashboard", "organizations", "accounts", "roles", "audit_logs"],
            buttons=["account:create", "account:disable", "role:edit"],
            data_scope=DataScope(type="all"),
        ),
        AdminRole(
            id="role_ops_admin",
            code="ops_admin",
            name="运营中心管理员",
            menus=["dashboard", "organizations", "accounts", "roles"],
            buttons=["account:create", "account:disable"],
            data_scope=DataScope(type="city", city_code="SY"),
        ),
        AdminRole(
            id="role_dealer_admin",
            code="dealer_admin",
            name="车行管理员",
            menus=["dashboard", "accounts"],
            buttons=["account:create"],
            data_scope=DataScope(type="organization", organization_id="org_dealer_a"),
        ),
    ]
    return {role.id: role for role in roles}


def _seed_accounts(
    organizations: dict[str, Organization],
    roles: dict[str, AdminRole],
) -> dict[str, AdminActor]:
    accounts = [
        AdminActor(
            account_id="acct_hq",
            username="hq_admin",
            display_name="总部管理员",
            organization=organizations["org_hq"],
            role=roles["role_hq_admin"],
            status="active",
        ),
        AdminActor(
            account_id="acct_ops",
            username="ops_admin",
            display_name="三亚运营",
            organization=organizations["org_sanya"],
            role=roles["role_ops_admin"],
            status="active",
        ),
        AdminActor(
            account_id="acct_disabled",
            username="disabled_admin",
            display_name="停用账号",
            organization=organizations["org_dealer_a"],
            role=roles["role_dealer_admin"],
            status="disabled",
        ),
        AdminActor(
            account_id="acct_dealer_active",
            username="dealer_active",
            display_name="海棠湾车行",
            organization=organizations["org_dealer_a"],
            role=roles["role_dealer_admin"],
            status="active",
        ),
    ]
    return {account.username: account for account in accounts}


def _password_hash(username: str) -> str:
    return _hash_password(f"{username}123")


def _hash_password(password: str) -> str:
    return sha256(f"rental-car:{password}".encode()).hexdigest()


def _is_org_visible(actor: AdminActor, organization: Organization) -> bool:
    scope = actor.role.data_scope
    if scope.type == "all":
        return True
    if scope.type == "city":
        return organization.city_code == scope.city_code or organization.id == actor.organization.id
    return organization.id == scope.organization_id


def _is_role_visible(actor: AdminActor, role: AdminRole) -> bool:
    scope_rank = {"organization": 1, "city": 2, "all": 3}
    actor_rank = scope_rank[actor.role.data_scope.type]
    role_rank = scope_rank[role.data_scope.type]
    return role_rank <= actor_rank


def _is_account_visible(actor: AdminActor, account: AdminActor) -> bool:
    return _is_org_visible(actor, account.organization)


admin_service = AdminService()
