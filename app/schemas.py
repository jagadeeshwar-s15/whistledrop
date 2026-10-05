from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models import ReportStatus


class ReportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    category: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=10, max_length=5000)
    evidence_url: HttpUrl | None = Field(default=None, max_length=2048)


class ReportCreated(BaseModel):
    case_code: str
    status: ReportStatus


class ReportTracking(BaseModel):
    case_code: str
    status: ReportStatus
    status_update: str | None
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class ModeratorReport(BaseModel):
    case_code: str
    category: str
    description: str
    evidence_url: str | None
    status: ReportStatus
    status_update: str | None
    created_at: datetime
    updated_at: datetime


class ModeratorReportUpdate(BaseModel):
    status: ReportStatus
    status_update: str | None = None
