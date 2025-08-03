// Power Flow SVG Visualization

class PowerFlowVisualization {
    constructor() {
        this.svg = document.getElementById('power-flow-svg');
        this.solarValue = document.getElementById('solar-value');
        this.homeValue = document.getElementById('home-value');
        this.gridValue = document.getElementById('grid-value');
        
        this.solarHomeCharge = document.getElementById('solar-home-line');
        this.solarGridLine = document.getElementById('solar-grid-line');
        this.gridHomeLine = document.getElementById('grid-home-line');
        
        this.particles = [];
        this.particleContainer = document.getElementById('flow-particles');
        
        // Initialize the visualization
        this.init();
    }
    
    init() {
        // Add hover effects to nodes
        this.addNodeInteractions();
        
        // Start with skeleton loading
        this.showSkeletons();
    }
    
    addNodeInteractions() {
        const nodes = this.svg.querySelectorAll('.power-node');
        nodes.forEach(node => {
            node.addEventListener('mouseenter', (e) => {
                const circle = node.querySelector('.node-bg');
                circle.style.transform = 'scale(1.1)';
            });
            
            node.addEventListener('mouseleave', (e) => {
                const circle = node.querySelector('.node-bg');
                circle.style.transform = 'scale(1)';
            });
        });
    }
    
    showSkeletons() {
        // Show loading skeletons while data loads
        this.updateNodeValue('solar-value', '<tspan class="skeleton skeleton-text small">Loading...</tspan>');
        this.updateNodeValue('home-value', '<tspan class="skeleton skeleton-text small">Loading...</tspan>');
        this.updateNodeValue('grid-value', '<tspan class="skeleton skeleton-text small">Loading...</tspan>');
    }
    
    updateNodeValue(nodeId, content) {
        const element = document.getElementById(nodeId);
        if (element) {
            element.innerHTML = content;
        }
    }
    
    updatePowerFlow(data) {
        const production = data.production_kw || 0;
        const consumption = data.consumption_kw || 0;
        const grid = data.grid_kw || 0;
        
        // Update node values with smooth transitions
        this.animateValueUpdate('solar-value', `${production.toFixed(1)} kW`);
        this.animateValueUpdate('home-value', `${consumption.toFixed(1)} kW`);
        this.animateValueUpdate('grid-value', `${Math.abs(grid).toFixed(1)} kW`);
        
        // Update flow lines based on power flow
        this.updateFlowLines(production, consumption, grid);
        
        // Animate particles along the flow paths
        this.animateParticles(production, consumption, grid);
    }
    
    animateValueUpdate(elementId, newValue) {
        const element = document.getElementById(elementId);
        if (element) {
            // Remove skeleton if present
            const skeleton = element.querySelector('.skeleton');
            if (skeleton) {
                skeleton.remove();
            }
            
            // Add updating class for animation
            element.classList.add('updating');
            
            setTimeout(() => {
                element.textContent = newValue;
                element.classList.remove('updating');
            }, 200);
        }
    }
    
    updateFlowLines(production, consumption, grid) {
        // Reset all lines
        [this.solarHomeCharge, this.solarGridLine, this.gridHomeLine].forEach(line => {
            if (line) {
                line.style.opacity = '0';
                line.classList.remove('active');
            }
        });
        
        const threshold = 0.1; // Minimum power to show flow
        
        // Solar to Home flow (always present if production > 0)
        if (production > threshold && this.solarHomeCharge) {
            this.solarHomeCharge.style.opacity = '1';
            this.solarHomeCharge.classList.add('active');
            this.solarHomeCharge.style.strokeWidth = Math.max(2, Math.min(8, production));
        }
        
        // Grid flows
        if (Math.abs(grid) > threshold) {
            if (grid > 0) {
                // Exporting to grid (Solar to Grid)
                if (this.solarGridLine) {
                    this.solarGridLine.style.opacity = '1';
                    this.solarGridLine.classList.add('active', 'export');
                    this.solarGridLine.classList.remove('import');
                    this.solarGridLine.style.strokeWidth = Math.max(2, Math.min(8, grid));
                }
            } else {
                // Importing from grid (Grid to Home)
                if (this.gridHomeLine) {
                    this.gridHomeLine.style.opacity = '1';
                    this.gridHomeLine.classList.add('active', 'import');
                    this.gridHomeLine.classList.remove('export');
                    this.gridHomeLine.style.strokeWidth = Math.max(2, Math.min(8, Math.abs(grid)));
                }
            }
        }
    }
    
    animateParticles(production, consumption, grid) {
        // Clear existing particles
        this.clearParticles();
        
        const threshold = 0.1;
        
        // Create particles for active flows
        if (production > threshold) {
            this.createParticleFlow('solar-home', 
                {x: 380, y: 85}, {x: 220, y: 165}, 
                Math.max(1, Math.min(3, Math.floor(production))));
        }
        
        if (grid > threshold) {
            // Export flow
            this.createParticleFlow('solar-grid', 
                {x: 420, y: 85}, {x: 580, y: 165}, 
                Math.max(1, Math.min(3, Math.floor(grid))));
        } else if (grid < -threshold) {
            // Import flow
            this.createParticleFlow('grid-home', 
                {x: 565, y: 200}, {x: 235, y: 200}, 
                Math.max(1, Math.min(3, Math.floor(Math.abs(grid)))));
        }
    }
    
    createParticleFlow(flowId, start, end, particleCount) {
        for (let i = 0; i < particleCount; i++) {
            setTimeout(() => {
                this.createParticle(start, end, flowId);
            }, i * 800); // Stagger particle creation
        }
    }
    
    createParticle(start, end, flowId) {
        const particle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        particle.classList.add('flow-particle');
        particle.setAttribute('r', '3');
        particle.setAttribute('cx', start.x);
        particle.setAttribute('cy', start.y);
        
        // Set particle color based on flow type
        if (flowId.includes('grid-home')) {
            particle.style.fill = 'var(--warning-amber)';
        } else {
            particle.style.fill = 'var(--solar-gold)';
        }
        
        this.particleContainer.appendChild(particle);
        
        // Animate particle along path
        const duration = 2000;
        const startTime = Date.now();
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function for smooth movement
            const eased = this.easeInOutCubic(progress);
            
            const x = start.x + (end.x - start.x) * eased;
            const y = start.y + (end.y - start.y) * eased;
            
            particle.setAttribute('cx', x);
            particle.setAttribute('cy', y);
            
            // Fade out near the end
            if (progress > 0.8) {
                particle.style.opacity = (1 - progress) * 5;
            }
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                // Remove particle when animation is complete
                particle.remove();
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
    }
    
    clearParticles() {
        // Remove all existing particles
        while (this.particleContainer.firstChild) {
            this.particleContainer.removeChild(this.particleContainer.firstChild);
        }
    }
    
    reset() {
        // Reset visualization to initial state
        this.clearParticles();
        [this.solarHomeCharge, this.solarGridLine, this.gridHomeLine].forEach(line => {
            if (line) {
                line.style.opacity = '0';
                line.classList.remove('active');
            }
        });
        this.showSkeletons();
    }
}

// Initialize power flow visualization when DOM is ready
let powerFlowViz;
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('power-flow-svg')) {
        powerFlowViz = new PowerFlowVisualization();
    }
});