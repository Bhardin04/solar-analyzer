// Panels JavaScript

let panelUpdateInterval;

// Initialize panels page
document.addEventListener('DOMContentLoaded', () => {
    updatePanelData();
    
    // Set up auto-refresh every 15 seconds for panel data
    panelUpdateInterval = setInterval(updatePanelData, 15000);
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (panelUpdateInterval) {
        clearInterval(panelUpdateInterval);
    }
});

// Update panel data
async function updatePanelData() {
    try {
        const panelReadings = await fetchAPI('/panels?limit=200');
        updatePanelSummary(panelReadings);
        updatePanelGrid(panelReadings);
        updatePanelTable(panelReadings);
        
    } catch (error) {
        console.error('Error updating panel data:', error);
        showNotification('Failed to update panel data', 'danger');
    }
}

// Update panel summary cards
function updatePanelSummary(panelReadings) {
    const totalPanels = new Set(panelReadings.map(p => p.panel_id)).size;
    const totalProduction = panelReadings.reduce((sum, p) => sum + p.power_w, 0);
    const averageProduction = totalPanels > 0 ? totalProduction / totalPanels : 0;
    
    // Calculate efficiency (assuming 400W rated power per panel)
    const ratedPower = totalPanels * 400;
    const efficiency = ratedPower > 0 ? (totalProduction / ratedPower) * 100 : 0;
    
    updateElement('#total-panels', totalPanels);
    updateElement('#total-panel-production', formatNumber(totalProduction, 0), '', ' W');
    updateElement('#average-panel-production', formatNumber(averageProduction, 0), '', ' W');
    updateElement('#panel-efficiency', formatNumber(efficiency, 1), '', '%');
}

// Update panel grid visualization
function updatePanelGrid(panelReadings) {
    const grid = document.getElementById('panel-grid');
    grid.innerHTML = '';
    
    // Group readings by panel_id and get the latest for each
    const latestReadings = {};
    panelReadings.forEach(reading => {
        if (!latestReadings[reading.panel_id] || 
            new Date(reading.timestamp) > new Date(latestReadings[reading.panel_id].timestamp)) {
            latestReadings[reading.panel_id] = reading;
        }
    });
    
    // Create panel items
    Object.values(latestReadings).forEach(reading => {
        const panelItem = document.createElement('div');
        panelItem.className = 'panel-item';
        
        // Determine panel status based on power output
        if (reading.power_w > 200) {
            panelItem.classList.add('producing');
        } else if (reading.power_w > 50) {
            panelItem.classList.add('low-production');
        } else {
            panelItem.classList.add('not-producing');
        }
        
        panelItem.innerHTML = `
            <div class="panel-id">${reading.panel_id}</div>
            <div class="panel-power">${formatNumber(reading.power_w, 0)}W</div>
        `;
        
        // Add click handler for panel details
        panelItem.addEventListener('click', () => {
            showPanelDetails(reading);
        });
        
        grid.appendChild(panelItem);
    });
}

// Update panel details table
function updatePanelTable(panelReadings) {
    const tbody = document.getElementById('panel-details-tbody');
    tbody.innerHTML = '';
    
    // Group readings by panel_id and get the latest for each
    const latestReadings = {};
    panelReadings.forEach(reading => {
        if (!latestReadings[reading.panel_id] || 
            new Date(reading.timestamp) > new Date(latestReadings[reading.panel_id].timestamp)) {
            latestReadings[reading.panel_id] = reading;
        }
    });
    
    // Sort by panel ID
    const sortedReadings = Object.values(latestReadings).sort((a, b) => 
        a.panel_id.localeCompare(b.panel_id)
    );
    
    sortedReadings.forEach(reading => {
        const row = document.createElement('tr');
        
        // Determine status
        let status = 'Normal';
        let statusClass = 'success';
        
        if (reading.power_w < 50) {
            status = 'Low Output';
            statusClass = 'warning';
        }
        
        if (reading.power_w === 0) {
            status = 'Not Producing';
            statusClass = 'danger';
        }
        
        row.innerHTML = `
            <td>${reading.panel_id}</td>
            <td>${reading.serial_number || '--'}</td>
            <td>${formatNumber(reading.power_w, 0)} W</td>
            <td>${reading.voltage_v ? formatNumber(reading.voltage_v, 1) + ' V' : '--'}</td>
            <td>${reading.current_a ? formatNumber(reading.current_a, 1) + ' A' : '--'}</td>
            <td>${reading.temperature_c ? formatNumber(reading.temperature_c, 1) + ' °C' : '--'}</td>
            <td><span class="badge bg-${statusClass}">${status}</span></td>
        `;
        
        tbody.appendChild(row);
    });
}

// Show panel details modal
function showPanelDetails(reading) {
    // Create a modal dynamically
    const modalHtml = `
        <div class="modal fade" id="panelModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Panel ${reading.panel_id} Details</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <table class="table">
                            <tbody>
                                <tr>
                                    <th>Panel ID:</th>
                                    <td>${reading.panel_id}</td>
                                </tr>
                                <tr>
                                    <th>Serial Number:</th>
                                    <td>${reading.serial_number || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th>Current Power:</th>
                                    <td>${formatNumber(reading.power_w, 0)} W</td>
                                </tr>
                                <tr>
                                    <th>Voltage:</th>
                                    <td>${reading.voltage_v ? formatNumber(reading.voltage_v, 1) + ' V' : 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th>Current:</th>
                                    <td>${reading.current_a ? formatNumber(reading.current_a, 1) + ' A' : 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th>Temperature:</th>
                                    <td>${reading.temperature_c ? formatNumber(reading.temperature_c, 1) + ' °C' : 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th>Last Update:</th>
                                    <td>${formatDateTime(reading.timestamp)}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('panelModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add new modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('panelModal'));
    modal.show();
    
    // Clean up when modal is closed
    document.getElementById('panelModal').addEventListener('hidden.bs.modal', () => {
        document.getElementById('panelModal').remove();
    });
}