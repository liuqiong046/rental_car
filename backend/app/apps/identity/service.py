"""In-memory identity verification service."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException, status

from app.apps.admin.schemas import AdminActor
from app.apps.identity.schemas import (
    IdentityAdminDetail,
    IdentityAssetPrepareRequest,
    IdentityAssetPrepareResponse,
    IdentityAuditLog,
    IdentityAuthorizePreviewRequest,
    IdentityReviewRequest,
    IdentitySubmission,
    IdentitySubmissionRequest,
)
from app.apps.users.schemas import CustomerProfile
from app.apps.users.service import customer_user_service


class IdentityVerificationService:
    def __init__(self) -> None:
        # TODO(WF-P0-07): 当前认证资料存在内存且图片为 mock URL；
        # 后续需补图片上传/授权查看、客户数据范围隔离、持久化和审核日志。
        self.submissions: dict[str, IdentitySubmission] = {}
        self.audit_logs: dict[str, list[IdentityAuditLog]] = {}

    def prepare_asset(
        self,
        customer: CustomerProfile,
        payload: IdentityAssetPrepareRequest,
    ) -> IdentityAssetPrepareResponse:
        asset_id = f"asset_{uuid4().hex[:12]}"
        safe_name = payload.file_name.replace("/", "_")
        asset_url = f"mock://identity-assets/{customer.user_id}/{asset_id}/{safe_name}"
        return IdentityAssetPrepareResponse(
            asset_url=asset_url,
            upload_url=f"{asset_url}?upload_token=mock",
            expires_in_seconds=900,
        )

    def submit(
        self,
        customer: CustomerProfile,
        payload: IdentitySubmissionRequest,
    ) -> IdentitySubmission:
        previous = self.submissions.get(customer.user_id)
        version = previous.version + 1 if previous else 1
        submission = IdentitySubmission(
            submission_id=f"ivs_{uuid4().hex[:10]}",
            user_id=customer.user_id,
            real_name=payload.real_name,
            id_no_mask=_mask_identity_no(payload.id_no),
            driver_license_no_mask=_mask_identity_no(payload.driver_license_no),
            id_card_front_url=_authorized_asset_url(payload.id_card_front_url),
            id_card_back_url=_authorized_asset_url(payload.id_card_back_url),
            driver_license_url=_authorized_asset_url(payload.driver_license_url),
            status="pending",
            updated_at=_now_iso(),
            version=version,
        )
        self.submissions[customer.user_id] = submission
        customer_user_service.update_certification_status(customer.user_id, "pending")
        return submission

    def get_for_customer(self, customer: CustomerProfile) -> IdentitySubmission:
        submission = self.submissions.get(customer.user_id)
        if submission is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="尚未提交身份认证")
        return submission

    def list_for_admin(self, actor: AdminActor) -> dict[str, object]:
        # P0 阶段暂按后台数据范围入口控制，完整客户城市隔离在客户域模型落库后补齐。
        _ = actor
        items = list(self.submissions.values())
        return {"items": items, "total": len(items)}

    def review(
        self,
        actor: AdminActor,
        submission_id: str,
        payload: IdentityReviewRequest,
    ) -> IdentitySubmission:
        submission = self._get_by_submission_id(submission_id)
        if payload.status == "rejected" and not payload.reject_reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="拒绝原因不能为空")
        updated = submission.model_copy(
            update={
                "status": payload.status,
                "reject_reason": payload.reject_reason if payload.status == "rejected" else None,
                "reviewed_by": actor.account_id,
                "reviewed_at": _now_iso(),
                "updated_at": _now_iso(),
            },
        )
        self.submissions[updated.user_id] = updated
        customer_user_service.update_certification_status(updated.user_id, payload.status)
        return updated

    def get_admin_detail(self, actor: AdminActor, submission_id: str) -> IdentityAdminDetail:
        _ = actor
        submission = self._get_by_submission_id(submission_id)
        customer = customer_user_service.get_user_by_id(submission.user_id)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="客户不存在")
        return IdentityAdminDetail(
            **submission.model_dump(),
            customer=customer,
            audit_logs=self.audit_logs.get(submission_id, []),
        )

    def authorize_preview(
        self,
        actor: AdminActor,
        submission_id: str,
        payload: IdentityAuthorizePreviewRequest,
    ) -> IdentitySubmission:
        submission = self._get_by_submission_id(submission_id)
        log = IdentityAuditLog(
            action="authorize_preview",
            actor_id=actor.account_id,
            reason=payload.reason,
            created_at=_now_iso(),
        )
        self.audit_logs[submission_id] = [*self.audit_logs.get(submission_id, []), log]
        return submission.model_copy(
            update={
                "id_card_front_url": _authorized_asset_url(submission.id_card_front_url, force=True),
                "id_card_back_url": _authorized_asset_url(submission.id_card_back_url, force=True),
                "driver_license_url": _authorized_asset_url(submission.driver_license_url, force=True),
            }
        )

    def _get_by_submission_id(self, submission_id: str) -> IdentitySubmission:
        for submission in self.submissions.values():
            if submission.submission_id == submission_id:
                return submission
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="认证记录不存在")


def _mask_identity_no(value: str) -> str:
    if len(value) <= 8:
        return f"{value[:2]}****{value[-2:]}"
    return f"{value[:4]}********{value[-4:]}"


def _authorized_asset_url(value: str, force: bool = False) -> str:
    if value.startswith("mock://identity/authorized-preview"):
        return value
    if value.startswith("mock://") and not force:
        return value
    return "mock://identity/authorized-preview"


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


identity_verification_service = IdentityVerificationService()
