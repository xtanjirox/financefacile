/**
 * Notifications handling for FinanceFacile
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize notifications
    initNotifications();
    
    // Set up event handlers
    setupMarkAllReadHandler();
});

/**
 * Initialize notifications by fetching them from the server
 */
function initNotifications() {
    // Check if we're on a page that should have notifications
    // Don't try to fetch notifications on the landing page or login page
    const currentPath = window.location.pathname;
    if (currentPath === '/' || currentPath === '/landing/' || currentPath.includes('/auth/login')) {
        console.log('Skipping notifications on landing/login page');
        return;
    }
    
    fetchNotifications();
    
    // Refresh notifications every 60 seconds
    setInterval(fetchNotifications, 60000);
}

/**
 * Fetch notifications from the server
 */
function fetchNotifications() {
    const container = document.getElementById('notification-list');
    const badge = document.getElementById('notification-badge');
    
    // If container doesn't exist, we're not on a page with notifications
    if (!container) {
        return;
    }
    
    // Show loading spinner
    container.innerHTML = `
        <div class="text-center py-3">
            <div class="spinner-border text-primary" role="status" style="color: #6259FF !important;">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    
    // Use the correct path to the notifications API
    fetch('/app/api/notifications/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin' // Include cookies for authentication
    })
        .then(response => {
            if (response.status === 403) {
                // User is not authenticated
                throw new Error('Authentication required');
            } else if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            updateNotificationBadge(data.unread_count);
            renderNotifications(data.notifications);
        })
        .catch(error => {
            console.error('Error fetching notifications:', error);
            
            // Hide badge when there's an error
            if (badge) {
                badge.style.display = 'none';
            }
            
            // Show appropriate error message
            if (error.message === 'Authentication required') {
                container.innerHTML = `
                    <div class="text-center py-3">
                        <div class="text-muted">Please log in to view notifications</div>
                    </div>
                `;
            } else {
                container.innerHTML = `
                    <div class="text-center py-3">
                        <div class="text-danger">Could not load notifications</div>
                        <small class="text-muted">Please try again later</small>
                    </div>
                `;
            }
        });
}

/**
 * Update the notification badge with the unread count
 */
function updateNotificationBadge(count) {
    const badge = document.getElementById('notification-badge');
    
    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'block';
    } else {
        badge.style.display = 'none';
    }
}

/**
 * Render notifications in the dropdown
 */
function renderNotifications(notifications) {
    const container = document.getElementById('notification-list');
    
    // Clear loading spinner
    container.innerHTML = '';
    
    if (notifications.length === 0) {
        container.innerHTML = '<div class="text-center py-4">No notifications</div>';
        return;
    }
    
    // Add each notification to the list
    notifications.forEach(notification => {
        const notificationElement = createNotificationElement(notification);
        container.appendChild(notificationElement);
    });
}

/**
 * Create a notification element
 */
function createNotificationElement(notification) {
    const element = document.createElement('a');
    element.href = '#';
    element.className = 'list-group-item list-group-item-action';
    
    if (!notification.is_read) {
        element.classList.add('bg-light');
    }
    
    // Format the notification based on its type
    let icon = '';
    switch(notification.type) {
        case 'event_invite':
            icon = '<i class="fas fa-calendar-alt me-2 text-primary" style="color: #6259FF !important;"></i>';
            break;
        case 'low_stock':
            icon = '<i class="fas fa-exclamation-triangle me-2 text-warning"></i>';
            break;
        case 'invoice_created':
            icon = '<i class="fas fa-file-invoice-dollar me-2 text-success"></i>';
            break;
        case 'expense_created':
            icon = '<i class="fas fa-money-bill-wave me-2 text-danger"></i>';
            break;
        default:
            icon = '<i class="fas fa-bell me-2 text-primary" style="color: #6259FF !important;"></i>';
    }
    
    // Create the notification content
    element.innerHTML = `
        <div class="d-flex align-items-start">
            <div class="flex-shrink-0">
                ${icon}
            </div>
            <div class="flex-grow-1 ms-2">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">${notification.title}</h6>
                    <small class="text-muted">${formatTimeAgo(notification.created_at)}</small>
                </div>
                <p class="mb-0 text-muted" style="font-size: 0.85rem;">${notification.message}</p>
            </div>
        </div>
    `;
    
    // Add click handler to mark as read and navigate
    element.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Send request to mark as read
        fetch(`/app/notifications/read/${notification.id}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (response.ok) {
                // Navigate to the notification URL
                if (notification.url) {
                    window.location.href = notification.url;
                } else {
                    // Refresh notifications if no URL
                    fetchNotifications();
                }
            }
        })
        .catch(error => {
            console.error('Error marking notification as read:', error);
        });
    });
    
    return element;
}

/**
 * Format a timestamp as a relative time (e.g., "2 hours ago")
 */
function formatTimeAgo(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) {
        return 'just now';
    }
    
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) {
        return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    }
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) {
        return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    }
    
    const days = Math.floor(hours / 24);
    if (days < 7) {
        return `${days} day${days !== 1 ? 's' : ''} ago`;
    }
    
    // If older than a week, just show the date
    return date.toLocaleDateString();
}

/**
 * Set up the "Mark all as read" button handler
 */
function setupMarkAllReadHandler() {
    const markAllReadButton = document.getElementById('mark-all-read');
    
    if (markAllReadButton) {
        markAllReadButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            fetch('/app/notifications/read-all/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (response.ok) {
                    // Refresh notifications
                    fetchNotifications();
                }
            })
            .catch(error => {
                console.error('Error marking all notifications as read:', error);
            });
        });
    }
}

/**
 * Get CSRF token from cookies
 */
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    
    return cookieValue || '';
}
