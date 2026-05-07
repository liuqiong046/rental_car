"""Identity verification API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.apps.admin.deps import require_admin_actor
from app.apps.admin.schemas import AdminActor
from app.apps.identity.schemas import (
    IdentityAdminDetail,
    IdentityAssetPrepareRequest,
    IdentityAssetPrepareResponse,
    IdentityAuthorizePreviewRequest,
    IdentityReviewRequest,
    IdentitySubmission,
    IdentitySubmissionListResponse,
    IdentitySubmissionRequest,
)
from app.apps.identity.service import identity_verification_service
from app.apps.users.deps import require_current_customer
from app.apps.users.schemas import CustomerProfile

router = APIRouter(prefix="/identity", tags=["identity"])


@router.post(
    "/assets",
    response_model=IdentityAssetPrepareResponse,
    status_code=status.HTTP_201_CREATED,
    summary="生成 C 端身份认证图片上传凭证",
)
async def prepare_identity_asset(
    payload: IdentityAssetPrepareRequest,
    customer: Annotated[CustomerProfile, Depends(require_current_customer)],
) -> IdentityAssetPrepareResponse:
    return identity_verification_service.prepare_asset(customer, payload)


@router.post(
    "/submissions",
    response_model=IdentitySubmission,
    status_code=status.HTTP_201_CREATED,
    summary="提交 C 端身份认证资料",
)
async def submit_identity(
    payload: IdentitySubmissionRequest,
    customer: Annotated[CustomerProfile, Depends(require_current_customer)],
) -> IdentitySubmission:
    return identity_verification_service.submit(customer, payload)


@router.get(
    "/me",
    response_model=IdentitySubmission,
    status_code=status.HTTP_200_OK,
    summary="查询 C 端身份认证状态",
)
async def read_my_identity(
    customer: Annotated[CustomerProfile, Depends(require_current_customer)],
) -> IdentitySubmission:
    return identity_verification_service.get_for_customer(customer)


@router.get(
    "/admin/submissions",
    response_model=IdentitySubmissionListResponse,
    status_code=status.HTTP_200_OK,
    summary="查询 PC 后台身份认证审核列表",
)
async def list_identity_submissions(
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> dict[str, object]:
    return identity_verification_service.list_for_admin(actor)


@router.get(
    "/admin/submissions/{submission_id}",
    response_model=IdentityAdminDetail,
    status_code=status.HTTP_200_OK,
    summary="查询 PC 后台身份认证客户详情",
)
async def get_identity_submission_detail(
    submission_id: str,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> IdentityAdminDetail:
    return identity_verification_service.get_admin_detail(actor, submission_id)


@router.post(
    "/admin/submissions/{submission_id}/authorize-preview",
    response_model=IdentitySubmission,
    status_code=status.HTTP_200_OK,
    summary="授权查看身份认证证件图片并记录审计",
)
async def authorize_identity_preview(
    submission_id: str,
    payload: IdentityAuthorizePreviewRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> IdentitySubmission:
    return identity_verification_service.authorize_preview(actor, submission_id, payload)


@router.post(
    "/admin/submissions/{submission_id}/review",
    response_model=IdentitySubmission,
    status_code=status.HTTP_200_OK,
    summary="PC 后台审核身份认证",
)
async def review_identity_submission(
    submission_id: str,
    payload: IdentityReviewRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> IdentitySubmission:
    return identity_verification_service.review(actor, submission_id, payload)
