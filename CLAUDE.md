# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Solar Analyzer is a Python application for monitoring and visualizing SunPower solar system data. It supports both cloud-based (MySunPower API) and local (PVS6 device) data access, with PostgreSQL for data storage and FastAPI for the web interface.

## Development Commands

```bash
# Install dependencies with uv
uv pip install -e .

# Run the application locally
uvicorn solar_analyzer.main:app --reload

# Run with Docker
docker-compose up -d

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "Description"

# Linting and formatting
ruff check src/
ruff format src/

# Run tests
pytest
```

## Code Architecture

### Directory Structure
```
src/solar_analyzer/
├── api/
│   ├── routes.py         # FastAPI endpoints
│   ├── sunpower_cloud.py # MySunPower API client
│   └── pvs6_local.py     # Local PVS6 device client
├── data/
│   ├── database.py       # Database connection
│   ├── models.py         # SQLAlchemy models
│   └── schemas.py        # Pydantic schemas
├── visualization/        # (Future) Dashboard components
├── config.py            # Application settings
└── main.py             # FastAPI application

alembic/                # Database migrations
tests/                  # Test files
```

### Key Components

1. **Data Sources**: 
   - MySunPower GraphQL API (requires manual token extraction)
   - PVS6 local device access (via HTTP on LAN)

2. **Database Models**:
   - `SolarReading`: System-level production/consumption data
   - `PanelReading`: Individual panel/microinverter data
   - `SystemStatus`: Status and alerts
   - `DataSource`: Track data source configurations

3. **API Endpoints** (all under `/api/v1/`):
   - Current/historical readings
   - Panel-level data
   - Energy statistics
   - Data synchronization

## Important Implementation Details

- Uses PostgreSQL with asyncpg for async database operations
- FastAPI with async/await throughout
- Pydantic for data validation
- Docker containerization for easy deployment
- Alembic for database migrations
- ruff for code formatting and linting

## Configuration

All configuration is managed through environment variables (see `.env.example`). The `Settings` class in `config.py` uses pydantic-settings for validation.

## Next Steps

- Implement automated data collection background tasks
- Create web-based visualization dashboard
- Add data export functionality
- Implement alert system for production issues