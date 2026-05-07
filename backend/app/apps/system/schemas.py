"""Pydantic DTOs for system endpoints."""

from pydantic import BaseModel, ConfigDict


class HealthCheckResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    service: str
    version: str

