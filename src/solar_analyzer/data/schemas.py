"""Pydantic schemas for API validation."""

from datetime import datetime

from pydantic import BaseModel, Field


class SolarReadingBase(BaseModel):
    """Base schema for solar readings."""

    timestamp: datetime
    production_kw: float = Field(..., ge=0)
    consumption_kw: float = Field(..., ge=0)
    grid_kw: float
    battery_kw: float | None = None
    battery_soc: float | None = Field(None, ge=0, le=100)


class SolarReadingCreate(SolarReadingBase):
    """Schema for creating solar readings."""

    pass


class SolarReading(SolarReadingBase):
    """Schema for solar reading responses."""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PanelReadingBase(BaseModel):
    """Base schema for panel readings."""

    timestamp: datetime
    panel_id: str
    serial_number: str | None = None
    power_w: float = Field(..., ge=0)
    voltage_v: float | None = Field(None, ge=0)
    current_a: float | None = Field(None, ge=0)
    temperature_c: float | None = None


class PanelReadingCreate(PanelReadingBase):
    """Schema for creating panel readings."""

    pass


class PanelReading(PanelReadingBase):
    """Schema for panel reading responses."""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SystemStatusBase(BaseModel):
    """Base schema for system status."""

    timestamp: datetime
    status: str = Field(..., pattern="^(OK|WARNING|ERROR)$")
    component: str
    message: str | None = None


class SystemStatusCreate(SystemStatusBase):
    """Schema for creating system status."""

    pass


class SystemStatus(SystemStatusBase):
    """Schema for system status responses."""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EnergyStats(BaseModel):
    """Schema for energy statistics."""

    period: str  # today, week, month, year
    total_production_kwh: float
    total_consumption_kwh: float
    total_export_kwh: float
    total_import_kwh: float
    self_consumption_rate: float
    peak_production_kw: float
    average_production_kw: float
