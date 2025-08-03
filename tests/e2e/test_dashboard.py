"""End-to-end tests for the dashboard."""

import pytest
from playwright.async_api import Page, expect


@pytest.mark.e2e
class TestDashboard:
    """Test dashboard functionality end-to-end."""

    async def test_dashboard_loads(self, page: Page):
        """Test that dashboard page loads successfully."""
        await page.goto("http://localhost:8000")

        # Check page title
        await expect(page).to_have_title("Dashboard - Solar Analyzer")

        # Check navigation
        await expect(page.locator(".navbar-brand")).to_contain_text("Solar Analyzer")

        # Check main sections are present
        await expect(page.locator("#current-production")).to_be_visible()
        await expect(page.locator("#current-consumption")).to_be_visible()
        await expect(page.locator("#grid-status")).to_be_visible()
        await expect(page.locator("#today-energy")).to_be_visible()

    async def test_dashboard_navigation(self, page: Page):
        """Test navigation between pages."""
        await page.goto("http://localhost:8000")

        # Test panels page navigation
        await page.click('a[href="/panels"]')
        await expect(page).to_have_url("http://localhost:8000/panels")
        await expect(page.locator("h2")).to_contain_text("Panel Performance")

        # Test history page navigation
        await page.click('a[href="/history"]')
        await expect(page).to_have_url("http://localhost:8000/history")

        # Test settings page navigation
        await page.click('a[href="/settings"]')
        await expect(page).to_have_url("http://localhost:8000/settings")

        # Return to dashboard
        await page.click('a[href="/"]')
        await expect(page).to_have_url("http://localhost:8000/")

    async def test_dashboard_data_loads(self, page: Page):
        """Test that dashboard loads data from API."""
        await page.goto("http://localhost:8000")

        # Wait for data to load (should replace "--" placeholders)
        await page.wait_for_function(
            "document.querySelector('#current-production').textContent !== '-- kW'",
            timeout=10000
        )

        # Check that data is displayed
        production_text = await page.text_content("#current-production")
        assert "kW" in production_text
        assert "--" not in production_text

        consumption_text = await page.text_content("#current-consumption")
        assert "kW" in consumption_text
        assert "--" not in consumption_text

        energy_text = await page.text_content("#today-energy")
        assert "kWh" in energy_text
        assert "--" not in energy_text

    async def test_dashboard_charts_render(self, page: Page):
        """Test that charts are rendered properly."""
        await page.goto("http://localhost:8000")

        # Wait for charts to load
        await page.wait_for_selector("canvas#production-chart", timeout=10000)
        await page.wait_for_selector("canvas#energy-distribution-chart", timeout=10000)

        # Check that canvas elements are present
        production_chart = page.locator("canvas#production-chart")
        await expect(production_chart).to_be_visible()

        distribution_chart = page.locator("canvas#energy-distribution-chart")
        await expect(distribution_chart).to_be_visible()

    async def test_dashboard_responsive_design(self, page: Page):
        """Test dashboard responsive design."""
        # Test desktop view
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.goto("http://localhost:8000")

        # Check that all cards are visible in row layout
        cards = page.locator(".row .col-md-3")
        assert await cards.count() == 4

        # Test tablet view
        await page.set_viewport_size({"width": 768, "height": 1024})
        await page.reload()

        # Cards should still be visible but may stack
        await expect(page.locator("#current-production")).to_be_visible()
        await expect(page.locator("#current-consumption")).to_be_visible()

        # Test mobile view
        await page.set_viewport_size({"width": 375, "height": 812})
        await page.reload()

        # Navigation should collapse
        hamburger = page.locator(".navbar-toggler")
        if await hamburger.is_visible():
            await hamburger.click()
            await expect(page.locator(".navbar-nav")).to_be_visible()

    async def test_dashboard_error_handling(self, page: Page):
        """Test dashboard error handling when API is unavailable."""
        # Mock API failure by intercepting requests
        await page.route("**/api/v1/current", lambda route: route.abort())
        await page.route("**/api/v1/stats/today", lambda route: route.abort())

        await page.goto("http://localhost:8000")

        # Check that error message appears
        await expect(page.locator(".alert-danger")).to_be_visible(timeout=10000)

        # System status should show error
        await page.wait_for_function(
            "document.querySelector('#system-status .badge').textContent === 'Error'",
            timeout=5000
        )

    async def test_dashboard_auto_refresh(self, page: Page):
        """Test that dashboard auto-refreshes data."""
        await page.goto("http://localhost:8000")

        # Wait for initial data load
        await page.wait_for_function(
            "document.querySelector('#current-production').textContent !== '-- kW'",
            timeout=10000
        )

        # Get initial production value
        initial_production = await page.text_content("#current-production")

        # Wait for auto-refresh (30 seconds + buffer)
        await page.wait_for_timeout(35000)

        # Check if data was refreshed (may be same value but timestamp should update)
        last_update = await page.text_content("#last-update")
        assert last_update != "--"


@pytest.mark.e2e
class TestPanelsPage:
    """Test panels page functionality."""

    async def test_panels_page_loads(self, page: Page):
        """Test that panels page loads successfully."""
        await page.goto("http://localhost:8000/panels")

        await expect(page.locator("h2")).to_contain_text("Panel Performance")

        # Check summary cards
        await expect(page.locator("#total-panels")).to_be_visible()
        await expect(page.locator("#total-panel-production")).to_be_visible()
        await expect(page.locator("#average-panel-production")).to_be_visible()
        await expect(page.locator("#panel-efficiency")).to_be_visible()

    async def test_panel_grid_display(self, page: Page):
        """Test panel grid visualization."""
        await page.goto("http://localhost:8000/panels")

        # Check that panel grid container exists
        await expect(page.locator("#panel-grid")).to_be_visible()

        # Panel grid should be populated with data
        await page.wait_for_function(
            "document.querySelector('#panel-grid').children.length > 0",
            timeout=10000
        )

    async def test_panel_details_table(self, page: Page):
        """Test panel details table."""
        await page.goto("http://localhost:8000/panels")

        # Check that table exists
        await expect(page.locator("#panel-details-table")).to_be_visible()

        # Table should have headers
        headers = ["Panel ID", "Serial Number", "Power (W)", "Temperature (°C)"]
        for header in headers:
            await expect(page.locator("th")).to_contain_text(header)


@pytest.mark.e2e
class TestHistoryPage:
    """Test history page functionality."""

    async def test_history_page_loads(self, page: Page):
        """Test that history page loads successfully."""
        await page.goto("http://localhost:8000/history")

        # Check that page loads (implementation may vary)
        await expect(page.locator("body")).to_be_visible()


@pytest.mark.e2e
class TestSettingsPage:
    """Test settings page functionality."""

    async def test_settings_page_loads(self, page: Page):
        """Test that settings page loads successfully."""
        await page.goto("http://localhost:8000/settings")

        # Check that page loads (implementation may vary)
        await expect(page.locator("body")).to_be_visible()


@pytest.mark.e2e
@pytest.mark.slow
class TestDashboardPerformance:
    """Test dashboard performance."""

    async def test_page_load_performance(self, page: Page):
        """Test that dashboard loads within acceptable time."""
        start_time = page.evaluate("Date.now()")

        await page.goto("http://localhost:8000")

        # Wait for critical content to load
        await page.wait_for_selector("#current-production")

        end_time = await page.evaluate("Date.now()")
        load_time = end_time - start_time

        # Should load within 5 seconds
        assert load_time < 5000, f"Page took {load_time}ms to load"

    async def test_api_response_time(self, page: Page):
        """Test API response times."""
        await page.goto("http://localhost:8000")

        # Measure API call performance
        await page.evaluate("""
            window.apiTimes = {};
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                const start = Date.now();
                return originalFetch(...args).then(response => {
                    const end = Date.now();
                    const url = args[0];
                    window.apiTimes[url] = end - start;
                    return response;
                });
            };
        """)

        # Trigger API calls
        await page.reload()
        await page.wait_for_timeout(2000)

        # Check API response times
        api_times = await page.evaluate("window.apiTimes || {}")

        for url, time in api_times.items():
            assert time < 2000, f"API call to {url} took {time}ms"


# Playwright configuration for these tests
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }
