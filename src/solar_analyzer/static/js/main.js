// Main JavaScript file for Solar Analyzer

// API Base URL
const API_BASE = '/api/v1';

// Utility Functions
const formatNumber = (num, decimals = 2) => {
    return Number(num).toFixed(decimals);
};

const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
};

const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString();
};

// API Helper Functions
async function fetchAPI(endpoint, options = {}) {
    try {
        const url = `${API_BASE}${endpoint}`;
        console.log('Fetching:', url);
        
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Response error:', errorText);
            throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        return data;
    } catch (error) {
        console.error('API Error for endpoint', endpoint, ':', error);
        throw error;
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Update element text with animation and skeleton removal
function updateElement(selector, value, prefix = '', suffix = '') {
    const element = document.querySelector(selector);
    if (element) {
        // Remove skeleton loading state
        const skeleton = element.querySelector('.skeleton');
        if (skeleton) {
            skeleton.remove();
        }
        
        // Add updating animation
        element.classList.add('updating');
        
        // Smooth transition
        setTimeout(() => {
            element.innerHTML = `<span class="metric-value">${prefix}${value}</span><span class="metric-unit">${suffix}</span>`;
            element.classList.remove('updating');
        }, 300);
    }
}

// Show skeleton loading state
function showSkeleton(selector, type = 'metric') {
    const element = document.querySelector(selector);
    if (element && !element.querySelector('.skeleton')) {
        element.innerHTML = `<div class="skeleton skeleton-${type} d-inline-block"></div>`;
    }
}

// Common initialization
document.addEventListener('DOMContentLoaded', () => {
    // Set current year in footer
    const yearElements = document.querySelectorAll('.current-year');
    yearElements.forEach(el => {
        el.textContent = new Date().getFullYear();
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});