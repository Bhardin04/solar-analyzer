"""SQLAlchemy models for solar data."""


from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from solar_analyzer.data.database import Base


class SolarReading(Base):
    """Model for storing solar production and consumption data."""

    __tablename__ = "solar_readings"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    production_kw = Column(Float, nullable=False)
    consumption_kw = Column(Float, nullable=False)
    grid_kw = Column(Float, nullable=False)  # Positive = export, Negative = import
    battery_kw = Column(Float, nullable=True)  # If battery is installed
    battery_soc = Column(Float, nullable=True)  # State of charge percentage
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("timestamp", name="uq_solar_reading_timestamp"),)


class PanelReading(Base):
    """Model for individual panel production data."""

    __tablename__ = "panel_readings"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    panel_id = Column(String(50), nullable=False, index=True)
    serial_number = Column(String(100), nullable=True)
    power_w = Column(Float, nullable=False)
    voltage_v = Column(Float, nullable=True)
    current_a = Column(Float, nullable=True)
    temperature_c = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("timestamp", "panel_id", name="uq_panel_reading"),
    )


class SystemStatus(Base):
    """Model for system status and alerts."""

    __tablename__ = "system_status"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # OK, WARNING, ERROR
    component = Column(String(100), nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DataSource(Base):
    """Model for tracking data sources and their status."""

    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(50), nullable=False)  # mysunpower_api, pvs6_local
    last_successful_fetch = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    is_active = Column(Integer, default=1)
    configuration = Column(Text, nullable=True)  # JSON configuration
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LogEntry(Base):
    """Model for storing application logs in database."""

    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    logger_name = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    module = Column(String(100), nullable=True)
    function = Column(String(100), nullable=True)
    line_number = Column(Integer, nullable=True)
    thread_id = Column(String(50), nullable=True)
    process_id = Column(Integer, nullable=True)
    user_id = Column(String(50), nullable=True)
    session_id = Column(String(100), nullable=True)
    request_id = Column(String(100), nullable=True)
    exception_type = Column(String(100), nullable=True)
    exception_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)  # Additional structured data
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_log_timestamp_level", "timestamp", "level"),
        Index("idx_log_logger_level", "logger_name", "level"),
        Index("idx_log_request", "request_id"),
    )


class PerformanceMetric(Base):
    """Model for storing performance metrics."""

    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram, timer
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)  # seconds, bytes, count, etc.
    tags = Column(JSON, nullable=True)  # Key-value pairs for categorization
    component = Column(String(100), nullable=True, index=True)
    operation = Column(String(100), nullable=True)
    duration_ms = Column(Float, nullable=True)
    success = Column(Integer, nullable=True)  # 1 for success, 0 for failure
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_perf_timestamp_metric", "timestamp", "metric_name"),
        Index("idx_perf_component_operation", "component", "operation"),
    )


class ApiRequestLog(Base):
    """Model for storing API request logs."""

    __tablename__ = "api_request_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    request_id = Column(String(100), nullable=False, unique=True, index=True)
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    query_params = Column(JSON, nullable=True)
    headers = Column(JSON, nullable=True)
    body_size = Column(Integer, nullable=True)
    response_status = Column(Integer, nullable=True, index=True)
    response_size = Column(Integer, nullable=True)
    duration_ms = Column(Float, nullable=False)
    user_agent = Column(String(500), nullable=True)
    client_ip = Column(String(45), nullable=True, index=True)  # IPv6 compatible
    user_id = Column(String(50), nullable=True, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_api_timestamp_status", "timestamp", "response_status"),
        Index("idx_api_path_method", "path", "method"),
    )


class SystemHealthMetric(Base):
    """Model for storing system health metrics."""

    __tablename__ = "system_health_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)  # cpu, memory, disk, network, database
    cpu_usage_percent = Column(Float, nullable=True)
    memory_usage_bytes = Column(Integer, nullable=True)
    memory_available_bytes = Column(Integer, nullable=True)
    disk_usage_bytes = Column(Integer, nullable=True)
    disk_available_bytes = Column(Integer, nullable=True)
    network_bytes_sent = Column(Integer, nullable=True)
    network_bytes_received = Column(Integer, nullable=True)
    database_connections_active = Column(Integer, nullable=True)
    database_connections_idle = Column(Integer, nullable=True)
    database_query_avg_time_ms = Column(Float, nullable=True)
    load_average = Column(Float, nullable=True)
    uptime_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_health_timestamp_type", "timestamp", "metric_type"),
    )
