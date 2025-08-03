# 🌞 Solar Analyzer

A comprehensive Python application to monitor, analyze, and visualize SunPower solar system data. Built with modern technologies for professional-grade solar energy monitoring.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

## ✨ Features

### 🔄 **Real-Time Monitoring**
- **WebSocket Integration**: Instant data updates without page refresh
- **Live Dashboard**: Real-time solar production, consumption, and grid monitoring
- **Connection Status**: Visual indicators for system health and connectivity
- **Auto-Reconnection**: Robust connection management with fallback to HTTP polling

### 📊 **Advanced Analytics**
- **Interactive Charts**: Chart.js visualizations with time-series data
- **Energy Statistics**: Daily, weekly, monthly, and yearly analysis
- **Panel-Level Monitoring**: Individual microinverter performance tracking
- **Animated Power Flow**: Dynamic SVG visualization with particle effects
- **Efficiency Metrics**: Self-consumption rates and optimization insights
- **Solar Design System**: Professional UI with solar-themed styling
- **Loading Skeletons**: Smooth loading states for better UX

### 🔌 **Multiple Data Sources**
- **PVS6 Local Access**: Direct connection to SunPower PVS6 monitoring device
- **MySunPower Cloud**: Legacy support for cloud-based data (until service shutdown)
- **Historical Import**: Bulk import capability for preserving historical data
- **Dual-Mode Operation**: Seamless switching between data sources

### 🗄️ **Professional Database System**
- **PostgreSQL Storage**: Reliable time-series data storage
- **Comprehensive Logging**: All application events stored in database
- **Performance Monitoring**: API response times and system metrics tracking
- **Data Retention**: Configurable retention policies for logs and metrics

### 🧪 **Enterprise Testing**
- **Comprehensive Test Suite**: Unit, integration, and end-to-end tests
- **Pytest Framework**: Professional testing with fixtures and mocks
- **Playwright E2E**: Browser automation for UI testing
- **Coverage Reporting**: 80% code coverage requirement

### 🚀 **Production Ready**
- **Docker Containerization**: Complete deployment solution
- **Database Migrations**: Alembic-managed schema evolution
- **Health Monitoring**: System health endpoints and metrics
- **Error Handling**: Graceful degradation and recovery

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PVS6 Device   │    │  MySunPower API  │    │   Web Browser   │
│  (172.27.153.1) │    │   (Cloud API)    │    │   (Dashboard)   │
└─────────┬───────┘    └─────────┬────────┘    └─────────┬───────┘
          │                      │                       │
          │ HTTP API             │ GraphQL               │ WebSocket/HTTP
          │                      │                       │
          └──────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │      FastAPI Server     │
                    │   (WebSocket + REST)    │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   PostgreSQL Database   │
                    │ (Time-series + Logging) │
                    └─────────────────────────┘
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/Bhardin04/solar-analyzer.git
cd solar-analyzer

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start with Docker Compose
docker-compose up -d

# Access the dashboard
open http://localhost:8000
```

### Option 2: Local Development

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/Bhardin04/solar-analyzer.git
cd solar-analyzer

# Install dependencies
uv sync

# Setup database (requires PostgreSQL running)
cp .env.example .env
# Configure DATABASE_URL in .env

# Run migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn src.solar_analyzer.main:app --host 0.0.0.0 --port 8000 --reload
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
# Database Configuration
DATABASE_URL=postgresql://solar_user:solar_password@localhost:5432/solar_analyzer

# PVS6 Local Access (Primary)
PVS6_HOST=172.27.153.1
PVS6_PORT=80

# MySunPower Cloud API (Legacy)
SUNPOWER_ACCESS_TOKEN=your_access_token_here
SUNPOWER_SITE_KEY=your_site_key_here

# Application Settings
APP_HOST=0.0.0.0
APP_PORT=8000
APP_ENV=development

# Logging Configuration
LOG_LEVEL=INFO
LOG_TO_DATABASE=true
LOG_RETENTION_DAYS=30
PERFORMANCE_MONITORING=true
```

## 🔌 PVS6 Setup Guide

### Step 1: Connect to PVS6 WiFi
1. Connect your computer to the SunPower WiFi network
2. Network name: Usually "SunPower" or similar
3. No password required for installer access

### Step 2: Test Connection
```bash
# Test PVS6 connectivity
uv run python debug_pvs6.py

# Test data sync
uv run python debug_sync.py
```

### Step 3: Start Monitoring
```bash
# Manual sync
curl -X POST http://localhost:8000/api/v1/sync/local

# Or use the web interface sync button
```

## 🌐 API Documentation

### Core Endpoints

- **`GET /`** - Interactive web dashboard
- **`WebSocket /ws`** - Real-time data streaming
- **`GET /api/v1/current`** - Latest solar reading
- **`GET /api/v1/readings`** - Historical data with time filters
- **`GET /api/v1/stats/{period}`** - Energy statistics (today/week/month/year)
- **`GET /api/v1/panels`** - Individual panel performance
- **`POST /api/v1/sync/local`** - Sync from PVS6 device
- **`POST /api/v1/sync/cloud`** - Sync from MySunPower cloud
- **`GET /health`** - System health check

### WebSocket Events

```javascript
// Connection to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// Event types received:
{
  "type": "current_data",
  "data": {
    "timestamp": "2025-08-03T12:00:00Z",
    "production_kw": 7.5,
    "consumption_kw": 2.3,
    "grid_kw": 5.2,
    "status": "active"
  }
}
```

## 🧪 Testing

### Run Test Suite

```bash
# All tests with coverage
uv run pytest

# Specific test types
uv run pytest tests/unit/ -m unit
uv run pytest tests/integration/ -m integration
uv run pytest tests/e2e/ -m e2e

# Generate reports
uv run pytest --cov-report=html
open htmlcov/index.html
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: API and database testing
- **End-to-End Tests**: Full browser automation with Playwright
- **Performance Tests**: Load testing and benchmarks

## 📊 Monitoring & Logging

### Database Logging Tables

- **`log_entries`**: Application logs with structured data
- **`api_request_logs`**: HTTP request/response tracking
- **`performance_metrics`**: System performance measurements
- **`system_health_metrics`**: CPU, memory, disk usage

### Query Examples

```sql
-- Recent errors
SELECT * FROM log_entries 
WHERE level = 'ERROR' 
ORDER BY timestamp DESC LIMIT 10;

-- API performance trends
SELECT DATE_TRUNC('hour', timestamp) as hour,
       AVG(duration_ms) as avg_response_time
FROM api_request_logs 
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY hour ORDER BY hour;
```

## 🗂️ Project Structure

```
solar-analyzer/
├── src/solar_analyzer/           # Main application code
│   ├── api/                      # API endpoints and WebSocket
│   ├── data/                     # Database models and schemas
│   ├── static/                   # Frontend assets (CSS, JS)
│   ├── templates/                # HTML templates
│   └── logging_*.py              # Logging system
├── tests/                        # Test suites
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── e2e/                      # End-to-end tests
├── alembic/                      # Database migrations
├── docker-compose.yml            # Docker deployment
├── ROADMAP.md                    # UI enhancement roadmap
├── TESTING.md                    # Testing documentation
└── pyproject.toml                # Python dependencies and config
```

## 🔧 Development

### Code Quality Tools

```bash
# Linting and formatting
uv run ruff check
uv run ruff format

# Type checking (if mypy configured)
uv run mypy src/

# Run pre-commit hooks
pre-commit run --all-files
```

### Database Operations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Check migration status
uv run alembic current
```

## 📈 Performance

### Benchmarks
- **Dashboard Load Time**: < 2 seconds
- **API Response Time**: < 200ms average
- **WebSocket Latency**: < 50ms
- **Database Query Time**: < 100ms average
- **Memory Usage**: ~150MB baseline

### Optimization Features
- **Connection Pooling**: Efficient database connections
- **Async Operations**: Non-blocking I/O throughout
- **Caching**: Response caching where appropriate
- **Batch Processing**: Efficient bulk operations

## 🚨 Troubleshooting

### Common Issues

**Connection to PVS6 fails**
```bash
# Check network connectivity
ping 172.27.153.1

# Verify you're on SunPower WiFi network
curl http://172.27.153.1/cgi-bin/dl_cgi?Command=DeviceList
```

**WebSocket connection drops**
- Check firewall settings
- Verify no proxy interference
- Network stability issues

**Database connection errors**
```bash
# Test PostgreSQL connection
PGPASSWORD=solar_password psql -U solar_user -h localhost -d solar_analyzer

# Check if database exists
uv run alembic current
```

**High memory usage**
- Check log retention settings
- Consider database cleanup scripts
- Monitor with `htop` or system tools

## 🛣️ Roadmap

See [ROADMAP.md](ROADMAP.md) for detailed UI enhancement plans including:
- Advanced power flow visualizations
- Predictive analytics dashboard
- Customizable widgets
- Mobile-responsive improvements
- Performance optimizations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run the test suite: `uv run pytest`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Submit a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Use conventional commit messages
- Ensure all tests pass

## 📄 License

This project is for personal use to monitor your own solar system. Built to preserve solar data access as SunPower transitions away from consumer services.

## 🙏 Acknowledgments

- Built in response to SunPower's business model changes
- Inspired by the need for data sovereignty in renewable energy
- Community-driven approach to solar monitoring
- Thanks to the open-source Python ecosystem

---

**⚡ Take control of your solar data with Solar Analyzer!** 🌞