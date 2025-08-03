"""Dashboard routes for web interface."""

from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from solar_analyzer.core import templates
from solar_analyzer.data.database import get_db

router = APIRouter(tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Render the main dashboard."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Solar Analyzer Dashboard",
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )


@router.get("/panels", response_class=HTMLResponse)
async def panels_view(request: Request, db: AsyncSession = Depends(get_db)):
    """Render the panels view."""
    return templates.TemplateResponse(
        "panels.html",
        {
            "request": request,
            "title": "Panel Performance",
        },
    )


@router.get("/history", response_class=HTMLResponse)
async def history_view(request: Request, db: AsyncSession = Depends(get_db)):
    """Render the history view."""
    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "title": "Historical Data",
        },
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_view(request: Request):
    """Render the settings view."""
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "title": "Settings",
        },
    )
