import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import engine, Base

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if they don't exist (Alembic handles migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured")
    yield
    await engine.dispose()


app = FastAPI(
    title="FinoMart Payment Method Health Monitor",
    description="Monitors 47 payment integrations across 6 Latin American markets",
    version="1.0.0",
    lifespan=lifespan,
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


@app.get("/")
async def health_check():
    return {"status": "ok", "service": "finomart-payment-monitor"}


# Register routers
from app.api.routes import transactions, metrics, insights, trends, roi, gaps, reports, admin  # noqa: E402

app.include_router(transactions.router, prefix="/api/v1", tags=["transactions"])
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
app.include_router(insights.router, prefix="/api/v1", tags=["insights"])
app.include_router(trends.router, prefix="/api/v1", tags=["trends"])
app.include_router(roi.router, prefix="/api/v1", tags=["roi"])
app.include_router(gaps.router, prefix="/api/v1", tags=["market-gaps"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
