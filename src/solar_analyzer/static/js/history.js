// History JavaScript

let productionHistoryChart, consumptionHistoryChart, gridHistoryChart, comparisonChart;

// Initialize history page
document.addEventListener('DOMContentLoaded', () => {
    initializeHistoryCharts();
    setupDateRangeForm();
    loadDefaultData();
});

// Initialize charts
function initializeHistoryCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    };

    // Production History Chart
    const productionCtx = document.getElementById('production-history-chart').getContext('2d');
    productionHistoryChart = new Chart(productionCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Production (kWh)',
                data: [],
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.1
            }]
        },
        options: chartOptions
    });

    // Consumption History Chart
    const consumptionCtx = document.getElementById('consumption-history-chart').getContext('2d');
    consumptionHistoryChart = new Chart(consumptionCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Consumption (kWh)',
                data: [],
                borderColor: '#17a2b8',
                backgroundColor: 'rgba(23, 162, 184, 0.1)',
                tension: 0.1
            }]
        },
        options: chartOptions
    });

    // Grid History Chart
    const gridCtx = document.getElementById('grid-history-chart').getContext('2d');
    gridHistoryChart = new Chart(gridCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Export (kWh)',
                data: [],
                backgroundColor: '#28a745'
            }, {
                label: 'Import (kWh)',
                data: [],
                backgroundColor: '#dc3545'
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Comparison Chart
    const comparisonCtx = document.getElementById('comparison-chart').getContext('2d');
    comparisonChart = new Chart(comparisonCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Production (kWh)',
                data: [],
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.1
            }, {
                label: 'Consumption (kWh)',
                data: [],
                borderColor: '#17a2b8',
                backgroundColor: 'rgba(23, 162, 184, 0.1)',
                tension: 0.1
            }]
        },
        options: chartOptions
    });
}

// Setup date range form
function setupDateRangeForm() {
    const form = document.getElementById('date-range-form');
    
    // Set default dates (last 7 days)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 7);
    
    document.getElementById('start-date').value = startDate.toISOString().split('T')[0];
    document.getElementById('end-date').value = endDate.toISOString().split('T')[0];
    
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        loadHistoricalData();
    });
}

// Load default data
function loadDefaultData() {
    loadHistoricalData();
}

// Load historical data
async function loadHistoricalData() {
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    const interval = document.getElementById('interval').value;
    
    if (!startDate || !endDate) {
        showNotification('Please select both start and end dates', 'warning');
        return;
    }
    
    try {
        // Show loading state
        showLoading(true);
        
        // Fetch readings
        const readings = await fetchAPI(`/readings?start=${startDate}T00:00:00Z&end=${endDate}T23:59:59Z&limit=1000`);
        
        // Process data based on interval
        const processedData = processHistoricalData(readings, interval);
        
        // Update charts
        updateHistoryCharts(processedData);
        
        // Update summary statistics
        updateHistorySummary(processedData);
        
        showLoading(false);
        
    } catch (error) {
        console.error('Error loading historical data:', error);
        showNotification('Failed to load historical data', 'danger');
        showLoading(false);
    }
}

// Process historical data based on interval
function processHistoricalData(readings, interval) {
    const data = {
        labels: [],
        production: [],
        consumption: [],
        export: [],
        import: []
    };
    
    if (readings.length === 0) {
        return data;
    }
    
    // Group readings by time interval
    const grouped = {};
    
    readings.forEach(reading => {
        const date = new Date(reading.timestamp);
        let key;
        
        switch(interval) {
            case 'hour':
                key = date.toISOString().slice(0, 13) + ':00:00Z';
                break;
            case 'day':
                key = date.toISOString().slice(0, 10);
                break;
            case 'week':
                const weekStart = new Date(date);
                weekStart.setDate(date.getDate() - date.getDay());
                key = weekStart.toISOString().slice(0, 10);
                break;
            case 'month':
                key = date.toISOString().slice(0, 7);
                break;
            default:
                key = date.toISOString().slice(0, 10);
        }
        
        if (!grouped[key]) {
            grouped[key] = {
                production: 0,
                consumption: 0,
                export: 0,
                import: 0,
                count: 0
            };
        }
        
        grouped[key].production += reading.production_kw;
        grouped[key].consumption += reading.consumption_kw;
        
        if (reading.grid_kw > 0) {
            grouped[key].export += reading.grid_kw;
        } else {
            grouped[key].import += Math.abs(reading.grid_kw);
        }
        
        grouped[key].count++;
    });
    
    // Convert to arrays
    Object.keys(grouped).sort().forEach(key => {
        const group = grouped[key];
        
        data.labels.push(formatDateLabel(key, interval));
        data.production.push(group.production / group.count); // Average for the period
        data.consumption.push(group.consumption / group.count);
        data.export.push(group.export / group.count);
        data.import.push(group.import / group.count);
    });
    
    return data;
}

// Format date label based on interval
function formatDateLabel(dateString, interval) {
    const date = new Date(dateString);
    
    switch(interval) {
        case 'hour':
            return date.toLocaleString();
        case 'day':
            return date.toLocaleDateString();
        case 'week':
            return `Week of ${date.toLocaleDateString()}`;
        case 'month':
            return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
        default:
            return date.toLocaleDateString();
    }
}

// Update history charts
function updateHistoryCharts(data) {
    // Production Chart
    productionHistoryChart.data.labels = data.labels;
    productionHistoryChart.data.datasets[0].data = data.production;
    productionHistoryChart.update();
    
    // Consumption Chart
    consumptionHistoryChart.data.labels = data.labels;
    consumptionHistoryChart.data.datasets[0].data = data.consumption;
    consumptionHistoryChart.update();
    
    // Grid Chart
    gridHistoryChart.data.labels = data.labels;
    gridHistoryChart.data.datasets[0].data = data.export;
    gridHistoryChart.data.datasets[1].data = data.import;
    gridHistoryChart.update();
    
    // Comparison Chart
    comparisonChart.data.labels = data.labels;
    comparisonChart.data.datasets[0].data = data.production;
    comparisonChart.data.datasets[1].data = data.consumption;
    comparisonChart.update();
}

// Update history summary
function updateHistorySummary(data) {
    const totalProduction = data.production.reduce((sum, val) => sum + val, 0);
    const totalConsumption = data.consumption.reduce((sum, val) => sum + val, 0);
    const totalExport = data.export.reduce((sum, val) => sum + val, 0);
    const totalImport = data.import.reduce((sum, val) => sum + val, 0);
    const netEnergy = totalProduction - totalConsumption;
    const selfConsumption = totalProduction > 0 ? ((totalProduction - totalExport) / totalProduction * 100) : 0;
    
    updateElement('#total-production', formatNumber(totalProduction, 1), '', ' kWh');
    updateElement('#total-consumption', formatNumber(totalConsumption, 1), '', ' kWh');
    updateElement('#net-energy', formatNumber(netEnergy, 1), '', ' kWh');
    updateElement('#self-consumption', formatNumber(selfConsumption, 1), '', '%');
}

// Show/hide loading state
function showLoading(show) {
    const button = document.querySelector('#date-range-form button[type="submit"]');
    if (show) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
    } else {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-sync"></i> Update';
    }
}

// Export functions
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('export-csv').addEventListener('click', exportCSV);
    document.getElementById('export-json').addEventListener('click', exportJSON);
});

// Export data as CSV
async function exportCSV() {
    try {
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        const readings = await fetchAPI(`/readings?start=${startDate}T00:00:00Z&end=${endDate}T23:59:59Z&limit=10000`);
        
        let csv = 'Timestamp,Production (kW),Consumption (kW),Grid (kW),Battery (kW),Battery SOC (%)\n';
        
        readings.forEach(reading => {
            csv += `${reading.timestamp},${reading.production_kw},${reading.consumption_kw},${reading.grid_kw},${reading.battery_kw || ''},${reading.battery_soc || ''}\n`;
        });
        
        downloadFile(csv, 'solar-data.csv', 'text/csv');
        
    } catch (error) {
        console.error('Error exporting CSV:', error);
        showNotification('Failed to export CSV', 'danger');
    }
}

// Export data as JSON
async function exportJSON() {
    try {
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        const readings = await fetchAPI(`/readings?start=${startDate}T00:00:00Z&end=${endDate}T23:59:59Z&limit=10000`);
        
        const json = JSON.stringify(readings, null, 2);
        downloadFile(json, 'solar-data.json', 'application/json');
        
    } catch (error) {
        console.error('Error exporting JSON:', error);
        showNotification('Failed to export JSON', 'danger');
    }
}

// Download file helper
function downloadFile(content, filename, contentType) {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}