// Dashboard JavaScript

let productionChart, energyDistributionChart, powerFlowChart;
let updateInterval;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    updateDashboard();
    
    // Set up auto-refresh every 30 seconds (fallback for when WebSocket is not available)
    updateInterval = setInterval(() => {
        // Only use polling if WebSocket is not connected
        if (!solarWebSocket || !solarWebSocket.isConnected) {
            updateDashboard();
        }
    }, 30000);
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});

// Initialize Charts
function initializeCharts() {
    // Production Chart
    const productionCtx = document.getElementById('production-chart').getContext('2d');
    productionChart = new Chart(productionCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Production (kW)',
                data: [],
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.1
            }, {
                label: 'Consumption (kW)',
                data: [],
                borderColor: '#17a2b8',
                backgroundColor: 'rgba(23, 162, 184, 0.1)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Power (kW)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                }
            }
        }
    });

    // Energy Distribution Chart
    const energyCtx = document.getElementById('energy-distribution-chart').getContext('2d');
    energyDistributionChart = new Chart(energyCtx, {
        type: 'doughnut',
        data: {
            labels: ['Self-Consumed', 'Exported', 'Imported'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: [
                    '#28a745',
                    '#ffc107',
                    '#dc3545'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Update dashboard data
async function updateDashboard() {
    console.log('Starting dashboard update...');
    
    try {
        // Fetch current reading
        console.log('Fetching current reading...');
        const currentReading = await fetchAPI('/current');
        console.log('Current reading received:', currentReading);
        updateCurrentValues(currentReading);
        
        // Fetch today's stats
        console.log('Fetching today stats...');
        const todayStats = await fetchAPI('/stats/today');
        console.log('Today stats received:', todayStats);
        updateTodayStats(todayStats);
        
        // Fetch recent readings for chart
        console.log('Fetching readings for chart...');
        const startOfDay = new Date();
        startOfDay.setHours(0, 0, 0, 0);
        const endOfDay = new Date();
        endOfDay.setHours(23, 59, 59, 999);
        
        const readings = await fetchAPI(`/readings?start=${encodeURIComponent(startOfDay.toISOString())}&end=${encodeURIComponent(endOfDay.toISOString())}&limit=100`);
        console.log('Readings received:', readings.length, 'items');
        updateProductionChart(readings);
        
        // Update status
        console.log('Dashboard update completed successfully');
        updateSystemStatus('OK');
        
    } catch (error) {
        console.error('Error updating dashboard:', error);
        updateSystemStatus('ERROR');
        showNotification(`Failed to update dashboard data: ${error.message}`, 'danger');
    }
}

// Update current values
function updateCurrentValues(reading) {
    if (!reading) {
        console.error('No reading data provided');
        return;
    }
    
    console.log('Updating current values with:', reading);
    
    updateElement('#current-production', formatNumber(reading.production_kw || 0, 2), '', ' kW');
    updateElement('#current-consumption', formatNumber(reading.consumption_kw || 0, 2), '', ' kW');
    
    // Update power flow visualization
    if (window.powerFlowViz) {
        powerFlowViz.updatePowerFlow(reading);
    }
    
    const gridValue = reading.grid_kw || 0;
    updateElement('#grid-status', formatNumber(Math.abs(gridValue), 2), '', ' kW');
    
    const gridCard = document.querySelector('#grid-status').closest('.card');
    if (gridCard) {
        gridCard.classList.remove('bg-success', 'bg-danger', 'bg-warning');
        if (gridValue > 0.1) {
            updateElement('#grid-direction', 'Exporting to grid');
            gridCard.classList.add('bg-success');
        } else if (gridValue < -0.1) {
            updateElement('#grid-direction', 'Importing from grid');
            gridCard.classList.add('bg-danger');
        } else {
            updateElement('#grid-direction', 'No grid exchange');
            gridCard.classList.add('bg-warning');
        }
    }
    
    updateElement('#last-update', formatDateTime(reading.timestamp));
}

// Update today's statistics
function updateTodayStats(stats) {
    if (!stats) {
        console.error('No stats data provided');
        return;
    }
    
    console.log('Updating today stats with:', stats);
    
    updateElement('#today-energy', formatNumber(stats.total_production_kwh || 0, 1), '', ' kWh');
    
    // Update energy distribution chart
    if (energyDistributionChart && energyDistributionChart.data) {
        const selfConsumed = (stats.total_production_kwh || 0) - (stats.total_export_kwh || 0);
        energyDistributionChart.data.datasets[0].data = [
            Math.max(0, selfConsumed),
            stats.total_export_kwh || 0,
            stats.total_import_kwh || 0
        ];
        energyDistributionChart.update();
    }
}

// Update production chart
function updateProductionChart(readings) {
    if (!readings || !Array.isArray(readings)) {
        console.error('No readings array provided');
        return;
    }
    
    console.log('Updating production chart with', readings.length, 'readings');
    
    const labels = [];
    const productionData = [];
    const consumptionData = [];
    
    // Get last 50 readings for better visualization
    const recentReadings = readings.slice(-50);
    
    recentReadings.forEach(reading => {
        const time = new Date(reading.timestamp);
        labels.push(time.toLocaleTimeString());
        productionData.push(reading.production_kw || 0);
        consumptionData.push(reading.consumption_kw || 0);
    });
    
    if (productionChart && productionChart.data) {
        productionChart.data.labels = labels;
        productionChart.data.datasets[0].data = productionData;
        productionChart.data.datasets[1].data = consumptionData;
        productionChart.update();
    }
}

// Update system status
function updateSystemStatus(status) {
    const statusElement = document.getElementById('system-status');
    statusElement.innerHTML = '';
    
    let badge;
    switch(status) {
        case 'OK':
            badge = '<span class="badge bg-success">Operational</span>';
            break;
        case 'WARNING':
            badge = '<span class="badge bg-warning">Warning</span>';
            break;
        case 'ERROR':
            badge = '<span class="badge bg-danger">Error</span>';
            break;
        default:
            badge = '<span class="badge bg-secondary">Unknown</span>';
    }
    
    statusElement.innerHTML = badge;
}

// Legacy power flow function - now handled by power-flow.js
// Kept for compatibility but unused
function createPowerFlow(production, consumption, grid) {
    // Power flow is now handled by the PowerFlowVisualization class
    // in power-flow.js - this function is deprecated
    console.log('Legacy createPowerFlow called - using new SVG visualization instead');
}