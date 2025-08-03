# Solar Analyzer

A Python application to monitor and visualize SunPower solar system data. Built with FastAPI, PostgreSQL, and Docker.

## Features

- **Multiple Data Sources**: Support for both MySunPower cloud API and local PVS6 device access
- **Real-time Monitoring**: Track production, consumption, grid usage, and battery status
- **Panel-level Monitoring**: View individual panel/microinverter performance
- **Historical Data**: Store and analyze historical solar production data
- **RESTful API**: Full API for data access and integration
- **Dockerized**: Easy deployment with Docker and docker-compose

## Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)
- uv package manager (for local development)
- PostgreSQL (included in docker-compose)

## Quick Start

1. Clone the repository
2. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

3. Configure your environment variables in `.env`:
   - For MySunPower API access:
     - `SUNPOWER_ACCESS_TOKEN`: Your MySunPower access token
     - `SUNPOWER_SITE_KEY`: Your site key
   - For local PVS6 access:
     - `PVS6_HOST`: IP address of your PVS6 device
     - `PVS6_PORT`: Port (usually 80)

4. Start the application:
   ```bash
   docker-compose up -d
   ```

5. Access the application at http://localhost:8000

## API Endpoints

- `GET /api/v1/current` - Get the most recent solar reading
- `GET /api/v1/readings` - Get historical readings with optional time range
- `POST /api/v1/readings` - Create a new reading
- `GET /api/v1/panels` - Get panel-level readings
- `POST /api/v1/panels` - Create panel readings
- `GET /api/v1/stats/{period}` - Get energy statistics (today/week/month/year)
- `GET /api/v1/status` - Get system status
- `POST /api/v1/sync/cloud` - Sync data from MySunPower API
- `POST /api/v1/sync/local` - Sync data from local PVS6

## Local Development

1. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   uv pip install -e .
   ```

3. Run database migrations:
   ```bash
   alembic upgrade head
   ```

4. Start the development server:
   ```bash
   uvicorn solar_analyzer.main:app --reload
   ```

## Getting SunPower API Credentials

### MySunPower API (Cloud)

1. Log into https://monitor.mysunpower.com
2. Open browser developer tools (F12)
3. Go to Network tab
4. Look for GraphQL requests
5. Extract:
   - Authorization header (Bearer token)
   - siteKey from request payload

### PVS6 Local Access

1. Connect to your PVS6 device's LAN1 installer port
2. The device typically has IP 172.27.153.1
3. No authentication required for local access

## Architecture

- **FastAPI**: Modern web framework for building APIs
- **PostgreSQL**: Time-series data storage
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migration management
- **httpx**: Async HTTP client for API calls
- **Docker**: Containerization for easy deployment

## Data Collection

The application supports two modes of data collection:

1. **Manual sync**: Use the `/api/v1/sync/*` endpoints to manually fetch data
2. **Automated collection**: Configure scheduled tasks (coming soon)

## Troubleshooting

- **Connection to PVS6 fails**: Ensure you're on the same network as the PVS6 device
- **MySunPower API errors**: Token may have expired, need to manually refresh
- **Database connection issues**: Check PostgreSQL is running and credentials are correct

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is for personal use to monitor your own solar system.