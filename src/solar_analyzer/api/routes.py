"""API routes for solar data access."""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from solar_analyzer.api.pvs6_local import PVS6LocalAPI
from solar_analyzer.api.sunpower_cloud import SunPowerCloudAPI
from solar_analyzer.data.database import get_db
from solar_analyzer.data.models import PanelReading as PanelReadingModel
from solar_analyzer.data.models import SolarReading as SolarReadingModel
from solar_analyzer.data.models import SystemStatus as SystemStatusModel
from solar_analyzer.data.schemas import (
    EnergyStats,
    PanelReading,
    PanelReadingCreate,
    SolarReading,
    SolarReadingCreate,
    SystemStatus,
)

router = APIRouter(prefix="/api/v1", tags=["solar"])


@router.get("/current", response_model=SolarReading)
async def get_current_reading(db: AsyncSession = Depends(get_db)):
    """Get the most recent solar reading."""
    result = await db.execute(
        select(SolarReadingModel).order_by(SolarReadingModel.timestamp.desc()).limit(1)
    )
    reading = result.scalar_one_or_none()
    if not reading:
        raise HTTPException(status_code=404, detail="No readings found")
    return reading


@router.get("/readings", response_model=List[SolarReading])
async def get_readings(
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get solar readings within a time range."""
    query = select(SolarReadingModel).order_by(SolarReadingModel.timestamp.desc())

    if start and end:
        query = query.where(
            and_(
                SolarReadingModel.timestamp >= start, SolarReadingModel.timestamp <= end
            )
        )
    elif start:
        query = query.where(SolarReadingModel.timestamp >= start)
    elif end:
        query = query.where(SolarReadingModel.timestamp <= end)

    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/readings", response_model=SolarReading)
async def create_reading(
    reading: SolarReadingCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new solar reading."""
    db_reading = SolarReadingModel(**reading.model_dump())
    db.add(db_reading)
    await db.commit()
    await db.refresh(db_reading)
    return db_reading


@router.get("/panels", response_model=List[PanelReading])
async def get_panel_readings(
    timestamp: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get panel readings."""
    query = select(PanelReadingModel).order_by(PanelReadingModel.timestamp.desc())

    if timestamp:
        # Get readings closest to the specified timestamp
        query = query.where(
            and_(
                PanelReadingModel.timestamp >= timestamp - timedelta(minutes=5),
                PanelReadingModel.timestamp <= timestamp + timedelta(minutes=5),
            )
        )

    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/panels", response_model=PanelReading)
async def create_panel_reading(
    reading: PanelReadingCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new panel reading."""
    db_reading = PanelReadingModel(**reading.model_dump())
    db.add(db_reading)
    await db.commit()
    await db.refresh(db_reading)
    return db_reading


@router.get("/stats/{period}", response_model=EnergyStats)
async def get_energy_stats(period: str, db: AsyncSession = Depends(get_db)):
    """Get energy statistics for a period (today, week, month, year)."""
    try:
        now = datetime.now()

        if period == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start = now - timedelta(days=7)
        elif period == "month":
            start = now - timedelta(days=30)
        elif period == "year":
            start = now - timedelta(days=365)
        else:
            raise HTTPException(status_code=400, detail="Invalid period")

        # Get all readings for the period
        result = await db.execute(
            select(SolarReadingModel).where(SolarReadingModel.timestamp >= start)
        )
        readings = result.scalars().all()
        
        if not readings:
            return EnergyStats(
                period=period,
                total_production_kwh=0.0,
                total_consumption_kwh=0.0,
                total_export_kwh=0.0,
                total_import_kwh=0.0,
                self_consumption_rate=0.0,
                peak_production_kw=0.0,
                average_production_kw=0.0,
            )

        # Calculate stats manually
        total_production = sum(r.production_kw for r in readings)
        total_consumption = sum(r.consumption_kw for r in readings)
        total_export = sum(max(0, r.grid_kw) for r in readings)
        total_import = sum(max(0, -r.grid_kw) for r in readings)
        peak_production = max(r.production_kw for r in readings)
        avg_production = total_production / len(readings) if readings else 0
        
        # Calculate self-consumption rate
        self_consumption_rate = (
            ((total_production - total_export) / total_production * 100)
            if total_production > 0
            else 0
        )

        return EnergyStats(
            period=period,
            total_production_kwh=total_production,
            total_consumption_kwh=total_consumption,
            total_export_kwh=total_export,
            total_import_kwh=total_import,
            self_consumption_rate=self_consumption_rate,
            peak_production_kw=peak_production,
            average_production_kw=avg_production,
        )
        
    except Exception as e:
        # Log the error and return empty stats
        print(f"Error in get_energy_stats: {e}")
        return EnergyStats(
            period=period,
            total_production_kwh=0.0,
            total_consumption_kwh=0.0,
            total_export_kwh=0.0,
            total_import_kwh=0.0,
            self_consumption_rate=0.0,
            peak_production_kw=0.0,
            average_production_kw=0.0,
        )


@router.get("/status", response_model=List[SystemStatus])
async def get_system_status(
    limit: int = Query(10, ge=1, le=100), db: AsyncSession = Depends(get_db)
):
    """Get recent system status entries."""
    result = await db.execute(
        select(SystemStatusModel)
        .order_by(SystemStatusModel.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/sync/cloud")
async def sync_cloud_data(db: AsyncSession = Depends(get_db)):
    """Sync data from MySunPower cloud API."""
    api = SunPowerCloudAPI()

    try:
        # Test connection
        if not await api.test_connection():
            raise HTTPException(
                status_code=503, detail="Unable to connect to SunPower API"
            )

        # Get current power data
        power_data = await api.get_current_power()
        site_data = power_data.get("data", {}).get("site", {})
        current = site_data.get("currentPower", {})

        if current:
            reading = SolarReadingCreate(
                timestamp=datetime.fromisoformat(current["timestamp"]),
                production_kw=current.get("production", 0) / 1000,
                consumption_kw=current.get("consumption", 0) / 1000,
                grid_kw=current.get("grid", 0) / 1000,
                battery_kw=current.get("battery", 0) / 1000 if "battery" in current else None,
                battery_soc=current.get("batterySOC") if "batterySOC" in current else None,
            )

            db_reading = SolarReadingModel(**reading.model_dump())
            db.add(db_reading)
            await db.commit()

        return {"status": "success", "message": "Data synced successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/local")
async def sync_local_data(db: AsyncSession = Depends(get_db)):
    """Sync data from local PVS6 device."""
    api = PVS6LocalAPI()

    try:
        # Test connection
        if not await api.test_connection():
            raise HTTPException(status_code=503, detail="Unable to connect to PVS6")

        # Get device data
        device_list = await api.get_device_list()
        data = await api.parse_device_data(device_list)

        # Create solar reading using power meter data
        reading = SolarReadingCreate(
            timestamp=datetime.now(),
            production_kw=data["total_power_kw"],
            consumption_kw=data["consumption_kw"],
            grid_kw=data["grid_kw"],
        )

        db_reading = SolarReadingModel(**reading.model_dump())
        db.add(db_reading)

        # Create panel readings from inverter data
        for inverter in data["inverters"]:
            panel_reading = PanelReadingCreate(
                timestamp=datetime.now(),
                panel_id=inverter["serial"],
                serial_number=inverter.get("module_serial", inverter["serial"]),
                power_w=inverter["power_w"],
                voltage_v=inverter.get("voltage_v", 0),
                current_a=inverter.get("current_a", 0),
                temperature_c=inverter.get("temperature_c", 0),
            )
            db_panel = PanelReadingModel(**panel_reading.model_dump())
            db.add(db_panel)

        await db.commit()
        return {"status": "success", "message": "Local data synced successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))