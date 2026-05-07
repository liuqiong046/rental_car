"""DTOs for identity verification with masked sensitive fields."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.apps.users.schemas import CustomerProfile

IdentityStatus = Literal["not_submitted", "pending", "approved", "rejected"]


class IdentitySubmissionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    real_name: str = Field(min_length=2, max_length=32)
    id_no: str = Field(min_length=6, max_length=32)
    driver_license_no: str = Field(min_length=6, max_length=32)
    id_card_front_url: str = Field(min_length=4, max_length=200)
    id_card_back_url: str = Field(min_length=4, max_length=200)
    driver_license_url: str = Field(min_length=4, max_length=200)


class IdentityReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["approved", "rejected"]
    reject_reason: str | None = Field(default=None, max_length=120)


class IdentityAssetPrepareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_name: str = Field(min_length=3, max_length=120)
    content_type: str = Field(pattern=r"^image/(jpeg|jpg|png|webp)$")


class IdentityAssetPrepareResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_url: str
    upload_url: str
    expires_in_seconds: int


class IdentityAuthorizePreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=2, max_length=120)


class IdentitySubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    submission_id: str
    user_id: str
    real_name: str
    id_no_mask: str
    driver_license_no_mask: str
    id_card_front_url: str
    id_card_back_url: str
    driver_license_url: str
    status: IdentityStatus
    reject_reason: str | None = None
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    updated_at: str
    version: int = 1


class IdentitySubmissionListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[IdentitySubmission]
    total: int


class IdentityAuditLog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    actor_id: str
    reason: str
    created_at: str


class IdentityAdminDetail(IdentitySubmission):
    model_config = ConfigDict(extra="forbid")

    customer: CustomerProfile
    audit_logs: list[IdentityAuditLog] = Field(default_factory=list)
