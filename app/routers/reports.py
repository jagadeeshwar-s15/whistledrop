from app.security import get_current_moderator
import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report, ReportStatus
from app.schemas import (
    ModeratorReport,
    ModeratorReportUpdate,
    ReportCreate,
    ReportCreated,
    ReportTracking,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

# 32 unambiguous characters (no 0/O, 1/I) -> 5 bits each; 16 chars = 80 bits of entropy.
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_MAX_CODE_ATTEMPTS = 5


def generate_case_code() -> str:
    chars = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(16))
    return "WD-" + "-".join(chars[i: i + 4] for i in range(0, 16, 4))


@router.post("", response_model=ReportCreated, status_code=status.HTTP_201_CREATED)
def create_report(payload: ReportCreate, db: Session = Depends(get_db)) -> Report:
    for _ in range(_MAX_CODE_ATTEMPTS):
        report = Report(
            case_code=generate_case_code(),
            category=payload.category,
            description=payload.description,
            evidence_url=str(
                payload.evidence_url) if payload.evidence_url else None,
            status=ReportStatus.SUBMITTED,
        )
        db.add(report)
        try:
            db.commit()
        except IntegrityError:
            # Case-code collision (astronomically unlikely): retry with a new code.
            db.rollback()
            continue
        except SQLAlchemyError:
            db.rollback()
            logger.exception("Failed to save report")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to save the report right now. Please try again later.",
            )
        return report

    logger.error("Could not generate a unique case code")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unable to save the report right now. Please try again later.",
    )


@router.get("", response_model=list[ModeratorReport])
def list_reports(
    status_filter: ReportStatus | None = None,
    category: str | None = None,
    _: str = Depends(get_current_moderator),
    db: Session = Depends(get_db),
) -> list[Report]:
    query = select(Report)

    if status_filter is not None:
        query = query.where(Report.status == status_filter)

    if category is not None:
        query = query.where(Report.category == category.strip())

    query = query.order_by(Report.created_at.desc())

    return list(db.scalars(query).all())


@router.patch("/{case_code}", response_model=ModeratorReport)
def update_report(
    case_code: str,
    report_update: ModeratorReportUpdate,
    _: str = Depends(get_current_moderator),
    db: Session = Depends(get_db),
) -> Report:
    report = db.scalar(
        select(Report).where(Report.case_code == case_code.strip().upper())
    )

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No report found for that case code.",
        )

    if report.status != ReportStatus.SUBMITTED:
        if report.status == ReportStatus.UNDER_REVIEW:
            if report_update.status not in {
                ReportStatus.RESOLVED,
                ReportStatus.DISMISSED,
            }:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status transition.",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This report is already closed.",
            )
    elif report_update.status != ReportStatus.UNDER_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A submitted report must first move to UNDER_REVIEW.",
        )

    report.status = report_update.status
    report.status_update = report_update.status_update

    db.commit()
    db.refresh(report)

    return report


@router.get("/{case_code}", response_model=ReportTracking)
def get_report(
    case_code: str = Path(min_length=1, max_length=32),
    db: Session = Depends(get_db),
) -> Report:
    try:
        report = db.scalar(
            select(Report).where(Report.case_code == case_code.strip().upper())
        )
    except SQLAlchemyError:
        logger.exception("Failed to look up report")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to look up the report right now. Please try again later.",
        )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No report found for that case code.",
        )
    return report
