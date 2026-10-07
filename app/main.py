from fastapi import FastAPI

from app.config import settings
from app.routers import auth, reports

app = FastAPI(
    title="WhistleDrop",
    description=(
        "A privacy-focused anonymous reporting backend. "
        "Submit reports without revealing your identity, "
        "track cases using a secure case code, and allow "
        "authorized moderators to review and manage reports."
    ),
    version="1.0.0",
    contact={
        "name": "WhistleDrop",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)
app.include_router(auth.router)
app.include_router(reports.router)


@app.get(
    "/health",
    tags=["❤️ System"],
    summary="Check API health",
    description="Returns the current health status of the WhistleDrop API.",
)
def health() -> dict[str, str]:
    return {"status": "ok"}
