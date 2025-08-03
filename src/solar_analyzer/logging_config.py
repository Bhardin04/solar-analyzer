"""Logging configuration for Solar Analyzer."""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict

import structlog
from rich.console import Console
from rich.logging import RichHandler

from solar_analyzer.config import settings
from solar_analyzer.logging_db_handler import DatabaseLogHandler


def setup_logging() -> None:
    """Set up structured logging with rich console output."""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging_config = get_logging_config()
    logging.config.dictConfig(logging_config)
    
    # Set log levels based on environment
    if settings.app_env == "development":
        logging.getLogger("solar_analyzer").setLevel(logging.DEBUG)
        logging.getLogger("uvicorn").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("solar_analyzer").setLevel(logging.INFO)
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration dictionary."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
            },
            "console": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "rich": {
                "format": "%(message)s",
                "datefmt": "[%X]",
            },
        },
        "handlers": {
            "console": {
                "class": "rich.logging.RichHandler",
                "level": "DEBUG" if settings.app_env == "development" else "INFO",
                "formatter": "rich",
                "console": Console(stderr=True),
                "show_time": True,
                "show_level": True,
                "show_path": True,
                "rich_tracebacks": True,
                "tracebacks_show_locals": True,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/solar_analyzer.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": "logs/errors.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "database": {
                "()": "solar_analyzer.logging_db_handler.DatabaseLogHandler",
                "level": "INFO",
                "batch_size": 50,
                "flush_interval": 10,
            },
        },
        "loggers": {
            "solar_analyzer": {
                "level": "DEBUG",
                "handlers": ["console", "file", "error_file", "database"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file", "database"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "file", "error_file", "database"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["file", "database"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["file", "database"],
                "propagate": False,
            },
            "httpx": {
                "level": "WARNING",
                "handlers": ["file", "database"],
                "propagate": False,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
    }


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Performance monitoring logger
perf_logger = get_logger("solar_analyzer.performance")

# API request logger
api_logger = get_logger("solar_analyzer.api")

# Database logger
db_logger = get_logger("solar_analyzer.database")

# Data sync logger
sync_logger = get_logger("solar_analyzer.sync")