# 🧪 Solar Analyzer Testing Framework

## Overview

The Solar Analyzer uses a comprehensive testing strategy with multiple types of tests, database logging, and performance monitoring.

## Testing Architecture

### Test Types

1. **Unit Tests** (`tests/unit/`)
   - Test individual functions and classes in isolation
   - Mock external dependencies
   - Fast execution, no database or network calls

2. **Integration Tests** (`tests/integration/`)
   - Test component interactions
   - Use test database
   - Test API endpoints with real database operations

3. **End-to-End Tests** (`tests/e2e/`)
   - Test complete user workflows
   - Use Playwright for browser automation
   - Test the full application stack

### Database Logging

All application logs, performance metrics, and system health data are stored in the PostgreSQL database for analysis and monitoring.

#### Log Tables

- **`log_entries`**: Application logs with structured data
- **`performance_metrics`**: Performance measurements and timings
- **`api_request_logs`**: HTTP request/response logging
- **`system_health_metrics`**: CPU, memory, disk, and network metrics

## Quick Start

### Install Dependencies

```bash
uv sync
```

### Run All Tests

```bash
# Run all tests with coverage
uv run pytest

# Run specific test type
uv run pytest tests/unit/ -m unit
uv run pytest tests/integration/ -m integration
uv run pytest tests/e2e/ -m e2e

# Run tests in parallel
uv run pytest -n auto

# Run tests with verbose output
uv run pytest -v
```

### Generate Reports

```bash
# Generate HTML coverage report
uv run pytest --cov-report=html

# Generate test report
uv run pytest --html=reports/pytest_report.html
```

## Test Configuration

### Pytest Configuration

Located in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--strict-markers",
    "--cov=src/solar_analyzer",
    "--cov-report=html:htmlcov",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
    "--html=reports/pytest_report.html",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests", 
    "e2e: End-to-end tests",
    "slow: Slow running tests",
    "database: Tests that require database",
    "external_api: Tests that call external APIs",
]
```

### Test Markers

Use markers to categorize and run specific test types:

```python
@pytest.mark.unit
def test_solar_reading_model():
    """Unit test for SolarReading model."""
    pass

@pytest.mark.integration
@pytest.mark.database
async def test_api_endpoint():
    """Integration test requiring database."""
    pass

@pytest.mark.e2e
@pytest.mark.slow
def test_dashboard_workflow():
    """End-to-end test of dashboard."""
    pass
```

## Writing Tests

### Unit Tests Example

```python
# tests/unit/test_models.py
import pytest
from solar_analyzer.data.models import SolarReading

@pytest.mark.unit
class TestSolarReading:
    async def test_create_solar_reading(self, test_db_session):
        reading = SolarReading(
            timestamp=datetime.now(),
            production_kw=5.5,
            consumption_kw=2.5,
            grid_kw=3.0,
        )
        
        test_db_session.add(reading)
        await test_db_session.commit()
        
        assert reading.id is not None
        assert reading.production_kw == 5.5
```

### Integration Tests Example

```python
# tests/integration/test_api.py
import pytest

@pytest.mark.integration
@pytest.mark.database
async def test_get_current_reading(async_test_client, sample_solar_readings):
    response = await async_test_client.get("/api/v1/current")
    
    assert response.status_code == 200
    data = response.json()
    assert "production_kw" in data
    assert "consumption_kw" in data
```

### End-to-End Tests Example

```python
# tests/e2e/test_dashboard.py
import pytest
from playwright.async_api import Page

@pytest.mark.e2e
async def test_dashboard_loads(page: Page):
    await page.goto("http://localhost:8000")
    
    # Check that dashboard elements are present
    await page.wait_for_selector("#current-production")
    await page.wait_for_selector("#current-consumption")
    
    # Verify data is loaded
    production_text = await page.text_content("#current-production")
    assert "kW" in production_text
```

## Fixtures

Common test fixtures are defined in `tests/conftest.py`:

### Database Fixtures

- `test_db_engine`: Test database engine
- `test_db_session`: Test database session
- `sample_solar_readings`: Sample data for testing
- `sample_panel_readings`: Sample panel data

### API Fixtures

- `test_client`: FastAPI test client
- `async_test_client`: Async HTTP test client
- `mock_pvs6_api`: Mocked PVS6 API
- `mock_sunpower_api`: Mocked SunPower API

### Usage Example

```python
async def test_api_with_data(async_test_client, sample_solar_readings):
    # sample_solar_readings automatically provides test data
    response = await async_test_client.get("/api/v1/readings")
    assert response.status_code == 200
    assert len(response.json()) > 0
```

## Performance Testing

### Performance Metrics

Use the performance logger to track metrics:

```python
from solar_analyzer.logging_db_handler import performance_logger

async def test_api_performance():
    start_time = time.time()
    
    # Test code here
    
    duration = (time.time() - start_time) * 1000
    await performance_logger.log_metric(
        metric_name="api_response_time",
        value=duration,
        unit="ms",
        component="api",
        operation="get_readings"
    )
```

### Load Testing

For load testing, use tools like Locust or Apache Bench:

```python
# load_test.py
from locust import HttpUser, task, between

class SolarAnalyzerUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def dashboard(self):
        self.client.get("/")
    
    @task
    def api_current(self):
        self.client.get("/api/v1/current")
    
    @task
    def api_stats(self):
        self.client.get("/api/v1/stats/today")
```

## Database Logging Analysis

### Query Log Data

```sql
-- Recent errors
SELECT * FROM log_entries 
WHERE level = 'ERROR' 
ORDER BY timestamp DESC 
LIMIT 10;

-- Performance trends
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    AVG(duration_ms) as avg_duration,
    COUNT(*) as request_count
FROM api_request_logs 
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour;

-- System health over time
SELECT 
    timestamp,
    cpu_usage_percent,
    memory_usage_bytes / (1024*1024*1024) as memory_gb,
    disk_usage_bytes / (1024*1024*1024) as disk_gb
FROM system_health_metrics 
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp;
```

### Log Dashboard Queries

Create monitoring dashboards using these queries:

```sql
-- Error rate by hour
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) FILTER (WHERE level = 'ERROR') as errors,
    COUNT(*) as total_logs,
    (COUNT(*) FILTER (WHERE level = 'ERROR') * 100.0 / COUNT(*)) as error_rate
FROM log_entries 
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY hour;

-- Top error messages
SELECT 
    message,
    COUNT(*) as occurrences,
    MAX(timestamp) as last_occurrence
FROM log_entries 
WHERE level = 'ERROR' 
    AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY message
ORDER BY occurrences DESC
LIMIT 10;
```

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install uv
      run: pip install uv
    
    - name: Install dependencies
      run: uv sync
    
    - name: Run tests
      run: uv run pytest
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Best Practices

### Test Organization

1. **One test per function/method**
2. **Clear test names describing what is tested**
3. **Use appropriate markers for test categorization**
4. **Mock external dependencies in unit tests**
5. **Use fixtures for common test data**

### Performance Testing

1. **Set performance benchmarks**
2. **Test with realistic data volumes**
3. **Monitor memory usage in long-running tests**
4. **Use database logging to track performance over time**

### Database Testing

1. **Use separate test database**
2. **Clean up test data after each test**
3. **Test database migrations**
4. **Verify database logging functionality**

## Troubleshooting

### Common Issues

1. **Test database connection errors**
   - Check PostgreSQL is running
   - Verify database credentials
   - Ensure test database exists

2. **Slow test execution**
   - Use pytest-xdist for parallel execution
   - Mock external API calls
   - Use smaller test datasets

3. **Database logging not working**
   - Check database permissions
   - Verify async session configuration
   - Check for circular import issues

### Debug Commands

```bash
# Run tests with debug output
uv run pytest -v -s

# Run specific test with debugging
uv run pytest tests/unit/test_models.py::TestSolarReading::test_create_solar_reading -v -s

# Check test database
psql -U solar_user -d solar_analyzer_test -c "SELECT COUNT(*) FROM log_entries;"

# View recent test logs
tail -f logs/solar_analyzer.log
```

## Reports and Coverage

Test reports are generated in:
- `htmlcov/`: HTML coverage report
- `reports/`: Test execution reports

View coverage report:
```bash
open htmlcov/index.html
```

## Monitoring in Production

Use database logging to monitor production systems:

1. **Set up log retention policies**
2. **Create alerting on error rates**
3. **Monitor performance metrics trends**
4. **Set up automated health checks**

Example log retention:
```sql
-- Delete logs older than 30 days
DELETE FROM log_entries WHERE timestamp < NOW() - INTERVAL '30 days';

-- Archive old performance metrics
CREATE TABLE performance_metrics_archive AS 
SELECT * FROM performance_metrics 
WHERE timestamp < NOW() - INTERVAL '90 days';

DELETE FROM performance_metrics 
WHERE timestamp < NOW() - INTERVAL '90 days';
```

This comprehensive testing framework ensures high code quality, performance monitoring, and reliable system operation.