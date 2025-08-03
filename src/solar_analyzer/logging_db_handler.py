"""Database logging handler for storing logs in PostgreSQL."""

import asyncio
import logging
import os
import threading
import traceback
import uuid
from datetime import datetime
from queue import Empty, Queue
from typing import Any

import psutil
from sqlalchemy.exc import SQLAlchemyError

from solar_analyzer.data.database import async_session
from solar_analyzer.data.models import LogEntry, PerformanceMetric, SystemHealthMetric


class DatabaseLogHandler(logging.Handler):
    """Custom logging handler that stores logs in database."""

    def __init__(self, batch_size: int = 100, flush_interval: int = 5):
        super().__init__()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.log_queue = Queue()
        self.shutdown_flag = threading.Event()

        # Start background thread for database writes
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def emit(self, record: logging.LogRecord) -> None:
        """Add log record to queue for database storage."""
        try:
            # Create log entry data
            log_data = self._format_log_record(record)
            self.log_queue.put(log_data)
        except Exception:
            # Don't let logging errors crash the application
            self.handleError(record)

    def _format_log_record(self, record: logging.LogRecord) -> dict[str, Any]:
        """Format log record for database storage."""
        # Extract exception information
        exception_type = None
        exception_message = None
        stack_trace = None

        if record.exc_info:
            exception_type = record.exc_info[0].__name__ if record.exc_info[0] else None
            exception_message = str(record.exc_info[1]) if record.exc_info[1] else None
            stack_trace = traceback.format_exception(*record.exc_info)
            stack_trace = ''.join(stack_trace) if stack_trace else None

        # Extract extra data
        extra_data = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            }:
                try:
                    # Only include JSON-serializable values
                    if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        extra_data[key] = value
                    else:
                        extra_data[key] = str(value)
                except Exception:
                    pass

        return {
            'timestamp': datetime.fromtimestamp(record.created),
            'level': record.levelname,
            'logger_name': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line_number': record.lineno,
            'thread_id': str(record.thread),
            'process_id': record.process,
            'user_id': getattr(record, 'user_id', None),
            'session_id': getattr(record, 'session_id', None),
            'request_id': getattr(record, 'request_id', None),
            'exception_type': exception_type,
            'exception_message': exception_message,
            'stack_trace': stack_trace,
            'extra_data': extra_data if extra_data else None,
        }

    def _worker(self) -> None:
        """Background worker to batch write logs to database."""
        loop = None
        batch = []

        while not self.shutdown_flag.is_set():
            try:
                # Collect logs from queue
                while len(batch) < self.batch_size:
                    try:
                        log_data = self.log_queue.get(timeout=self.flush_interval)
                        batch.append(log_data)
                    except Empty:
                        break

                # Write batch to database if we have logs
                if batch:
                    if loop is None:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    loop.run_until_complete(self._write_logs_to_db(batch))
                    batch.clear()

            except Exception as e:
                # Log error to stderr to avoid recursive logging
                if "atexit" not in str(e):  # Don't spam atexit errors during shutdown
                    print(f"DatabaseLogHandler error: {e}", file=os.sys.stderr)

        # Cleanup
        if loop:
            loop.close()

    async def _write_logs_to_db(self, logs: list) -> None:
        """Write log batch to database."""
        try:
            async with async_session() as session:
                # Create LogEntry objects
                log_entries = [LogEntry(**log_data) for log_data in logs]

                # Add to session and commit
                session.add_all(log_entries)
                await session.commit()

        except SQLAlchemyError as e:
            # Log to stderr to avoid recursive logging
            if "atexit" not in str(e):
                print(f"Failed to write logs to database: {e}", file=os.sys.stderr)
        except Exception as e:
            # Log to stderr to avoid recursive logging
            if "atexit" not in str(e):
                print(f"Database logging error: {e}", file=os.sys.stderr)

    def close(self) -> None:
        """Close the handler and clean up resources."""
        self.shutdown_flag.set()
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=10)
        super().close()


class PerformanceLogger:
    """Logger for performance metrics."""

    def __init__(self):
        self.session_factory = async_session

    async def log_metric(
        self,
        metric_name: str,
        value: float,
        metric_type: str = "gauge",
        unit: str | None = None,
        tags: dict[str, Any] | None = None,
        component: str | None = None,
        operation: str | None = None,
        duration_ms: float | None = None,
        success: bool | None = None,
        error_message: str | None = None,
    ) -> None:
        """Log a performance metric to database."""
        try:
            async with self.session_factory() as session:
                metric = PerformanceMetric(
                    timestamp=datetime.now(),
                    metric_name=metric_name,
                    metric_type=metric_type,
                    value=value,
                    unit=unit,
                    tags=tags,
                    component=component,
                    operation=operation,
                    duration_ms=duration_ms,
                    success=1 if success is True else (0 if success is False else None),
                    error_message=error_message,
                )

                session.add(metric)
                await session.commit()

        except Exception as e:
            print(f"Failed to log performance metric: {e}", file=os.sys.stderr)

    async def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        request_id: str | None = None,
        user_id: str | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Log an API request to database."""
        try:
            from solar_analyzer.data.models import ApiRequestLog

            async with self.session_factory() as session:
                log_entry = ApiRequestLog(
                    timestamp=datetime.now(),
                    request_id=request_id or str(uuid.uuid4()),
                    method=method,
                    path=path,
                    response_status=status_code,
                    duration_ms=duration_ms,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    user_id=user_id,
                    error_message=error_message,
                )

                session.add(log_entry)
                await session.commit()

        except Exception as e:
            print(f"Failed to log API request: {e}", file=os.sys.stderr)


class SystemHealthLogger:
    """Logger for system health metrics."""

    def __init__(self):
        self.session_factory = async_session

    async def log_system_health(self) -> None:
        """Log current system health metrics."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else None

            async with self.session_factory() as session:
                health_metric = SystemHealthMetric(
                    timestamp=datetime.now(),
                    metric_type="system",
                    cpu_usage_percent=cpu_percent,
                    memory_usage_bytes=memory.used,
                    memory_available_bytes=memory.available,
                    disk_usage_bytes=disk.used,
                    disk_available_bytes=disk.free,
                    network_bytes_sent=network.bytes_sent,
                    network_bytes_received=network.bytes_recv,
                    load_average=load_avg,
                    uptime_seconds=int(psutil.boot_time()),
                )

                session.add(health_metric)
                await session.commit()

        except Exception as e:
            print(f"Failed to log system health: {e}", file=os.sys.stderr)


# Global instances
performance_logger = PerformanceLogger()
health_logger = SystemHealthLogger()
