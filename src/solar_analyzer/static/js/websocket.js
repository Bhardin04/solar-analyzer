// WebSocket real-time data connection
class SolarWebSocket {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.isConnected = false;
        this.heartbeatInterval = null;
        this.callbacks = {
            onConnect: [],
            onDisconnect: [],
            onData: [],
            onError: [],
            onAlert: []
        };
    }
    
    connect() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            console.log('Connecting to WebSocket:', wsUrl);
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = this.onOpen.bind(this);
            this.ws.onmessage = this.onMessage.bind(this);
            this.ws.onclose = this.onClose.bind(this);
            this.ws.onerror = this.onError.bind(this);
            
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.scheduleReconnect();
        }
    }
    
    onOpen() {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        
        // Start heartbeat
        this.startHeartbeat();
        
        // Request initial data
        this.send({ type: 'request_data' });
        
        // Notify callbacks
        this.callbacks.onConnect.forEach(callback => callback());
        
        // Update UI
        this.updateConnectionStatus('connected');
    }
    
    onMessage(event) {
        try {
            const message = JSON.parse(event.data);
            console.log('WebSocket message received:', message.type);
            
            switch (message.type) {
                case 'current_data':
                case 'solar_update':
                    this.callbacks.onData.forEach(callback => callback(message.data));
                    break;
                    
                case 'system_alert':
                    this.callbacks.onAlert.forEach(callback => callback(message.alert));
                    break;
                    
                case 'pong':
                    // Heartbeat response
                    console.log('Heartbeat pong received');
                    break;
                    
                default:
                    console.log('Unknown message type:', message.type);
            }
            
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }
    
    onClose(event) {
        console.log('WebSocket disconnected', event.code, event.reason);
        this.isConnected = false;
        this.stopHeartbeat();
        
        // Notify callbacks
        this.callbacks.onDisconnect.forEach(callback => callback());
        
        // Update UI
        this.updateConnectionStatus('disconnected');
        
        // Schedule reconnect if not a clean close
        if (event.code !== 1000) {
            this.scheduleReconnect();
        }
    }
    
    onError(error) {
        console.error('WebSocket error:', error);
        this.callbacks.onError.forEach(callback => callback(error));
        this.updateConnectionStatus('error');
    }
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
            return true;
        }
        return false;
    }
    
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.send({ type: 'ping' });
            }
        }, 30000); // Ping every 30 seconds
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.updateConnectionStatus('failed');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
        
        console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
        this.updateConnectionStatus('reconnecting');
        
        setTimeout(() => {
            if (!this.isConnected) {
                this.connect();
            }
        }, delay);
    }
    
    updateConnectionStatus(status) {
        // Update connection indicator in UI
        const indicator = document.getElementById('connection-status');
        if (indicator) {
            indicator.className = `connection-status status-${status}`;
            
            const messages = {
                connected: 'Live',
                disconnected: 'Disconnected',
                reconnecting: 'Reconnecting...',
                error: 'Connection Error',
                failed: 'Connection Failed'
            };
            
            indicator.textContent = messages[status] || status;
        }
        
        // Update system status if available
        const systemStatus = document.getElementById('system-status');
        if (systemStatus && status === 'connected') {
            systemStatus.innerHTML = '<span class="badge bg-success">Online</span>';
        } else if (systemStatus && status !== 'connected') {
            systemStatus.innerHTML = '<span class="badge bg-warning">Offline</span>';
        }
    }
    
    // Event listener management
    on(event, callback) {
        if (this.callbacks[event]) {
            this.callbacks[event].push(callback);
        }
    }
    
    off(event, callback) {
        if (this.callbacks[event]) {
            const index = this.callbacks[event].indexOf(callback);
            if (index > -1) {
                this.callbacks[event].splice(index, 1);
            }
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
        }
        this.stopHeartbeat();
    }
}

// Global WebSocket instance
let solarWebSocket = null;

// Initialize WebSocket when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize WebSocket on dashboard page
    if (window.location.pathname === '/' || window.location.pathname.includes('dashboard')) {
        initializeWebSocket();
    }
});

function initializeWebSocket() {
    solarWebSocket = new SolarWebSocket();
    
    // Set up event handlers
    solarWebSocket.on('onConnect', () => {
        console.log('WebSocket connected - real-time updates enabled');
        showNotification('Real-time updates connected', 'success');
    });
    
    solarWebSocket.on('onDisconnect', () => {
        console.log('WebSocket disconnected - falling back to polling');
        showNotification('Real-time updates disconnected', 'warning');
    });
    
    solarWebSocket.on('onData', (data) => {
        console.log('Received real-time solar data:', data);
        updateDashboardWithRealtimeData(data);
    });
    
    solarWebSocket.on('onAlert', (alert) => {
        console.log('Received system alert:', alert);
        showNotification(alert.message, alert.level || 'warning');
    });
    
    solarWebSocket.on('onError', (error) => {
        console.error('WebSocket error:', error);
        showNotification('Real-time connection error', 'danger');
    });
    
    // Connect
    solarWebSocket.connect();
}

function updateDashboardWithRealtimeData(data) {
    // Update current values with real-time data
    if (typeof updateCurrentValues === 'function') {
        updateCurrentValues(data);
    }
    
    // Update timestamp
    const timestampElement = document.getElementById('last-update');
    if (timestampElement) {
        const updateTime = new Date(data.timestamp);
        timestampElement.textContent = updateTime.toLocaleString();
    }
    
    // Update connection status
    const dataSourceElement = document.getElementById('data-source');
    if (dataSourceElement) {
        dataSourceElement.textContent = 'Real-time (WebSocket)';
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (solarWebSocket) {
        solarWebSocket.disconnect();
    }
});