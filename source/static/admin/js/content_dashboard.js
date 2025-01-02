 // Content Dashboard JavaScript

// Store chart instances globally for cleanup
let contentMetricsChart = null;
let contentTypeChart = null;

function initializeContentForm(config) {
    const { contentId, csrfToken, apiEndpoints, assetAnalytics } = config;
    
    // Initialize components
    initializeBasicForm();
    initializeAIGeneration(contentId, csrfToken, apiEndpoints);
    initializeAssetManagement(contentId, csrfToken, apiEndpoints);
    initializeEnhancedServices(contentId, csrfToken, apiEndpoints);
    initializeCharts();

    // Initialize animations
    initializeAnimations();
    
    // Initialize analytics if available
    if (assetAnalytics) {
        // No need to initialize charts again
    }

    // Add resize handler for charts
    window.addEventListener('resize', debounce(() => {
        if (contentMetricsChart) {
            contentMetricsChart.resize();
        }
        if (contentTypeChart) {
            contentTypeChart.resize();
        }
    }, 250));
}

function initializeAnimations() {
    // Initialize AOS
    AOS.init({
        duration: 800,
        once: true,
        offset: 100,
        easing: 'ease-out-cubic'
    });

    // Add fade-in animation to cards
    document.querySelectorAll('.card').forEach((card, index) => {
        card.setAttribute('data-aos', 'fade-up');
        card.setAttribute('data-aos-delay', (index * 100).toString());
    });

    // Add hover animations to buttons
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            btn.style.transform = 'translateY(-2px)';
            btn.style.boxShadow = 'var(--shadow-lg)';
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.transform = 'translateY(0)';
            btn.style.boxShadow = 'var(--shadow-md)';
        });
    });
}

function initializeBasicForm() {
    const form = document.getElementById('content-form');
    if (!form) return;

    // Add form validation
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!validateForm(form)) return;
        
        showLoadingState(form);
        try {
            await handleFormSubmit(form, apiEndpoints.save, csrfToken);
            showSuccessMessage('Content saved successfully');
        } catch (error) {
            showErrorMessage(error.message || 'Failed to save content');
        } finally {
            hideLoadingState(form);
        }
    });

    // Add real-time validation
    form.querySelectorAll('input, select, textarea').forEach(field => {
        field.addEventListener('input', () => validateField(field));
        field.addEventListener('blur', () => validateField(field));
    });
}

function validateForm(form) {
    let isValid = true;
    form.querySelectorAll('input, select, textarea').forEach(field => {
        if (!validateField(field)) isValid = false;
    });
    return isValid;
}

function validateField(field) {
    const value = field.value.trim();
    const isRequired = field.hasAttribute('required');
    const isValid = !isRequired || value !== '';
    
    field.classList.toggle('is-invalid', !isValid);
    
    const feedback = field.nextElementSibling;
    if (feedback?.classList.contains('invalid-feedback')) {
        feedback.style.display = isValid ? 'none' : 'block';
    }
    
    return isValid;
}

function initializeAIGeneration(contentId, csrfToken, apiEndpoints) {
    const generationSection = document.querySelector('.generation-section');
    if (!generationSection) return;

    const startBtn = document.getElementById('start-generation');
    const progressBar = generationSection.querySelector('.progress-bar');
    const statusText = generationSection.querySelector('.status');
    const timeRemaining = generationSection.querySelector('.time-remaining');

    if (startBtn) {
        startBtn.addEventListener('click', async () => {
            const prompt = document.getElementById('prompt')?.value;
            if (!prompt) {
                showErrorMessage('Please enter a prompt');
                return;
            }

            try {
                startBtn.disabled = true;
                updateGenerationStatus('processing');
                
                // Simulate progress updates
                const progressInterval = simulateProgress(progressBar, timeRemaining);
                
                await handleContentGeneration(contentId, apiEndpoints.generate, csrfToken);
                
                clearInterval(progressInterval);
                progressBar.style.width = '100%';
                updateGenerationStatus('complete');
                showSuccessMessage('Content generated successfully');
            } catch (error) {
                updateGenerationStatus('error');
                showErrorMessage(error.message || 'Generation failed');
            } finally {
                startBtn.disabled = false;
            }
        });
    }
}

function simulateProgress(progressBar, timeRemaining) {
    let progress = 0;
    const interval = setInterval(() => {
        if (progress < 90) {
            progress += Math.random() * 5;
            progressBar.style.width = `${progress}%`;
            
            const remainingSeconds = Math.ceil((100 - progress) / 5);
            timeRemaining.textContent = `${remainingSeconds}s remaining`;
        }
    }, 1000);
    return interval;
}

function initializeAssetManagement(contentId, csrfToken, apiEndpoints) {
    const assetGrid = document.querySelector('.asset-grid');
    if (!assetGrid) return;

    // Initialize sortable grid
    new Sortable(assetGrid, {
        animation: 150,
        ghostClass: 'asset-item-ghost',
        onEnd: async (evt) => {
            const newOrder = Array.from(assetGrid.children).map(item => item.dataset.assetId);
            try {
                await updateAssetOrder(newOrder, apiEndpoints.assets, csrfToken);
                showSuccessMessage('Asset order updated');
            } catch (error) {
                showErrorMessage('Failed to update asset order');
                // Revert to original order
                evt.item.parentNode.insertBefore(evt.item, evt.oldIndex < evt.newIndex ? evt.oldNextSibling : evt.oldPreviousS);
            }
        }
    });

    // Initialize asset preview
    assetGrid.querySelectorAll('.asset-item').forEach(item => {
        item.addEventListener('click', () => {
            showAssetPreview(item);
        });
    });
}

function showAssetPreview(assetItem) {
    const modal = new bootstrap.Modal(document.createElement('div'));
    modal.element.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Asset Preview</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="asset-preview-large">
                        ${assetItem.querySelector('.asset-preview').innerHTML}
                    </div>
                    <div class="asset-details">
                        ${assetItem.querySelector('.asset-info').innerHTML}
                    </div>
                </div>
            </div>
        </div>
    `;
    modal.show();
}

function initializeEnhancedServices(contentId, csrfToken, apiEndpoints) {
    const services = {
        'validate-content': {
            endpoint: '/api/content/validate/',
            successMessage: 'Content validation successful',
            errorMessage: 'Validation failed'
        },
        'enhance-content': {
            endpoint: '/api/content/enhance/',
            successMessage: 'Content enhanced successfully',
            errorMessage: 'Enhancement failed',
            requiresReload: true
        },
        'optimize-assets': {
            endpoint: '/api/assets/optimize/',
            successMessage: 'Assets optimized successfully',
            errorMessage: 'Optimization failed',
            requiresReload: true
        },
        'analyze-assets': {
            endpoint: '/api/assets/analyze/',
            successMessage: 'Asset analysis complete',
            errorMessage: 'Analysis failed',
            callback: updateAssetAnalytics
        }
    };

    Object.entries(services).forEach(([id, config]) => {
        initializeServiceButton(id, config, contentId, csrfToken);
    });
}

function initializeServiceButton(id, config, contentId, csrfToken) {
    const button = document.getElementById(id);
    if (!button) return;

    button.addEventListener('click', async () => {
        try {
            button.disabled = true;
            addLoadingSpinner(button);

            const response = await fetch(config.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ content_id: contentId })
            });

            const result = await response.json();
            if (result.success) {
                showSuccessMessage(config.successMessage);
                if (config.callback) config.callback(result.data);
                if (config.requiresReload) location.reload();
            } else {
                throw new Error(result.error || config.errorMessage);
            }
        } catch (error) {
            showErrorMessage(error.message);
        } finally {
            button.disabled = false;
            removeLoadingSpinner(button);
        }
    });
}

function addLoadingSpinner(button) {
    const originalContent = button.innerHTML;
    button.dataset.originalContent = originalContent;
    button.innerHTML = `
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        Loading...
    `;
}

function removeLoadingSpinner(button) {
    button.innerHTML = button.dataset.originalContent;
    delete button.dataset.originalContent;
}

function showSuccessMessage(message) {
    showNotification(message, 'success');
}

function showErrorMessage(message) {
    showNotification(message, 'danger');
    console.error(message); // Log error to console for debugging
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Trigger reflow to start animation
    notification.offsetHeight;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

async function handleFormSubmit(form, endpoint, csrfToken) {
    const formData = new FormData(form);
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        });

        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'An error occurred');
        }
        return result;
    } catch (error) {
        showErrorMessage(error.message || 'Failed to submit form');
        throw error; // Rethrow error for further handling
    }
}

function initializeCharts() {
    // Clean up existing charts
    if (contentMetricsChart) {
        contentMetricsChart.destroy();
        contentMetricsChart = null;
    }
    if (contentTypeChart) {
        contentTypeChart.destroy();
        contentTypeChart = null;
    }

    // Initialize metrics chart
    const metricsCtx = document.getElementById('contentMetricsChart');
    if (metricsCtx) {
        const parentWidth = metricsCtx.parentElement.offsetWidth;
        metricsCtx.style.width = '100%';
        metricsCtx.style.height = Math.min(400, parentWidth * 0.6) + 'px';

        contentMetricsChart = new Chart(metricsCtx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Content Created',
                    data: [12, 19, 3, 5, 2, 3],
                    borderColor: 'rgb(45, 152, 218)',
                    backgroundColor: 'rgba(45, 152, 218, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Content Completed',
                    data: [8, 15, 2, 4, 1, 2],
                    borderColor: 'rgb(46, 204, 113)',
                    backgroundColor: 'rgba(46, 204, 113, 0.1)',
                    tension: 0.4,
                    fill: true
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
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }

    // Initialize type chart
    const typeCtx = document.getElementById('contentTypeChart');
    if (typeCtx) {
        const parentWidth = typeCtx.parentElement.offsetWidth;
        typeCtx.style.width = '100%';
        typeCtx.style.height = Math.min(400, parentWidth * 0.6) + 'px';

        contentTypeChart = new Chart(typeCtx, {
            type: 'doughnut',
            data: {
                labels: ['Video', 'Audio', 'Text'],
                datasets: [{
                    data: [12, 19, 3],
                    backgroundColor: [
                        'rgb(45, 152, 218)',
                        'rgb(46, 204, 113)',
                        'rgb(155, 89, 182)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    }
                },
                cutout: '70%'
            }
        });
    }
}

// Update chart data without recreating the entire chart
function updateChartData(chart, newData) {
    if (!chart) return;

    chart.data.datasets.forEach((dataset, index) => {
        dataset.data = newData[index] || [];
    });
    chart.update('none'); // Update without animation for better performance
}

// Debounce function for resize handling
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    
    // Add smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});