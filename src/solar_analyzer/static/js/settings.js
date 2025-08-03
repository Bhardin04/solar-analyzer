// Settings JavaScript

// Initialize settings page
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    setupEventHandlers();
    loadSystemInfo();
});

// Load current settings
async function loadSettings() {
    // Load settings from localStorage or API
    const settings = getStoredSettings();
    
    if (settings.sunpowerToken) {
        document.getElementById('sunpower-token').value = settings.sunpowerToken;
    }
    if (settings.sunpowerSiteKey) {
        document.getElementById('sunpower-site-key').value = settings.sunpowerSiteKey;
    }
    if (settings.pvs6Host) {
        document.getElementById('pvs6-host').value = settings.pvs6Host;
    }
    if (settings.pvs6Port) {
        document.getElementById('pvs6-port').value = settings.pvs6Port;
    }
    if (settings.collectionInterval) {
        document.getElementById('collection-interval').value = settings.collectionInterval;
    }
    if (settings.retentionDays) {
        document.getElementById('retention-days').value = settings.retentionDays;
    }
}

// Get stored settings from localStorage
function getStoredSettings() {
    const stored = localStorage.getItem('solarAnalyzerSettings');
    return stored ? JSON.parse(stored) : {};
}

// Save settings to localStorage
function saveSettings(settings) {
    localStorage.setItem('solarAnalyzerSettings', JSON.stringify(settings));
}

// Setup event handlers
function setupEventHandlers() {
    // Test connection buttons
    document.getElementById('test-sunpower').addEventListener('click', testSunPowerConnection);
    document.getElementById('test-pvs6').addEventListener('click', testPVS6Connection);
    
    // Action buttons
    document.getElementById('sync-now').addEventListener('click', syncNow);
    document.getElementById('clear-cache').addEventListener('click', clearCache);
    document.getElementById('confirm-reset').addEventListener('click', resetAllData);
    
    // Auto-save settings on change
    const settingsInputs = ['sunpower-token', 'sunpower-site-key', 'pvs6-host', 'pvs6-port', 'collection-interval', 'retention-days'];
    settingsInputs.forEach(id => {
        document.getElementById(id).addEventListener('change', saveCurrentSettings);
    });
}

// Save current settings
function saveCurrentSettings() {
    const settings = {
        sunpowerToken: document.getElementById('sunpower-token').value,
        sunpowerSiteKey: document.getElementById('sunpower-site-key').value,
        pvs6Host: document.getElementById('pvs6-host').value,
        pvs6Port: document.getElementById('pvs6-port').value,
        collectionInterval: document.getElementById('collection-interval').value,
        retentionDays: document.getElementById('retention-days').value
    };
    
    saveSettings(settings);
    showNotification('Settings saved', 'success');
}

// Test SunPower connection
async function testSunPowerConnection() {
    const button = document.getElementById('test-sunpower');
    const status = document.getElementById('sunpower-status');
    
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Testing...';
    
    try {
        // This would normally call the API with the provided credentials
        // For now, just simulate the test
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Try to sync cloud data
        const response = await fetchAPI('/sync/cloud', { method: 'POST' });
        
        status.innerHTML = '<div class="alert alert-success">Connection successful!</div>';
        showNotification('SunPower connection test successful', 'success');
        
    } catch (error) {
        status.innerHTML = '<div class="alert alert-danger">Connection failed: ' + error.message + '</div>';
        showNotification('SunPower connection test failed', 'danger');
    } finally {
        button.disabled = false;
        button.innerHTML = 'Test';
    }
}

// Test PVS6 connection
async function testPVS6Connection() {
    const button = document.getElementById('test-pvs6');
    const status = document.getElementById('pvs6-status');
    
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Testing...';
    
    try {
        // Try to sync local data
        const response = await fetchAPI('/sync/local', { method: 'POST' });
        
        status.innerHTML = '<div class="alert alert-success">Connection successful!</div>';
        showNotification('PVS6 connection test successful', 'success');
        
    } catch (error) {
        status.innerHTML = '<div class="alert alert-danger">Connection failed: ' + error.message + '</div>';
        showNotification('PVS6 connection test failed', 'danger');
    } finally {
        button.disabled = false;
        button.innerHTML = 'Test';
    }
}

// Load system information
async function loadSystemInfo() {
    try {
        // Get app info
        const appInfo = await fetchAPI('/', { 
            headers: {},
            method: 'GET'
        });
        
        updateElement('#app-version', appInfo.version || '0.1.0');
        
        // Get database stats (you would implement this endpoint)
        // For now, just show placeholder data
        updateElement('#db-records', 'Loading...');
        updateElement('#oldest-record', 'Loading...');
        updateElement('#last-sync', 'Loading...');
        
        // Try to get some actual stats
        setTimeout(async () => {
            try {
                const readings = await fetchAPI('/readings?limit=1');
                if (readings.length > 0) {
                    updateElement('#last-sync', formatDateTime(readings[0].timestamp));
                } else {
                    updateElement('#last-sync', 'No data yet');
                }
            } catch (error) {
                updateElement('#last-sync', 'Unknown');
            }
        }, 1000);
        
    } catch (error) {
        console.error('Error loading system info:', error);
    }
}

// Sync now
async function syncNow() {
    const button = document.getElementById('sync-now');
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Syncing...';
    
    try {
        const settings = getStoredSettings();
        let synced = false;
        
        // Try cloud sync if configured
        if (settings.sunpowerToken && settings.sunpowerSiteKey) {
            try {
                await fetchAPI('/sync/cloud', { method: 'POST' });
                showNotification('Cloud data synced successfully', 'success');
                synced = true;
            } catch (error) {
                console.error('Cloud sync failed:', error);
            }
        }
        
        // Try local sync if configured
        if (settings.pvs6Host) {
            try {
                await fetchAPI('/sync/local', { method: 'POST' });
                showNotification('Local data synced successfully', 'success');
                synced = true;
            } catch (error) {
                console.error('Local sync failed:', error);
            }
        }
        
        if (!synced) {
            showNotification('No data sources configured or available', 'warning');
        }
        
        // Refresh system info
        loadSystemInfo();
        
    } catch (error) {
        console.error('Sync error:', error);
        showNotification('Sync failed', 'danger');
    } finally {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-sync"></i> Sync Now';
    }
}

// Clear cache
function clearCache() {
    const button = document.getElementById('clear-cache');
    button.disabled = true;
    
    // Clear localStorage
    localStorage.removeItem('solarAnalyzerSettings');
    
    // Clear any cached data
    if ('caches' in window) {
        caches.keys().then(names => {
            names.forEach(name => {
                caches.delete(name);
            });
        });
    }
    
    showNotification('Cache cleared successfully', 'success');
    
    setTimeout(() => {
        button.disabled = false;
    }, 1000);
}

// Reset all data
async function resetAllData() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('resetModal'));
    modal.hide();
    
    try {
        // This would call an API endpoint to reset all data
        // For now, just show a message
        showNotification('Data reset functionality not implemented yet', 'warning');
        
    } catch (error) {
        console.error('Reset error:', error);
        showNotification('Reset failed', 'danger');
    }
}