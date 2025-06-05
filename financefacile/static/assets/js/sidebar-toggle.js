/**
 * Sidebar Toggle System - Complete Rewrite
 * Features:
 * - Vanilla JavaScript implementation
 * - Responsive behavior for desktop and mobile
 * - State persistence using localStorage
 * - Mobile overlay with click-outside-to-close
 * - Touch support for mobile devices
 */
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const body = document.body;
    const sidebar = document.getElementById('sidebar');
    const toggleButtons = document.querySelectorAll('.js-sidebar-toggle');
    const wrapper = document.querySelector('.wrapper');
    
    // Constants
    const STORAGE_KEY = 'sidebarState';
    const MOBILE_BREAKPOINT = 768;
    
    // State
    let isMobile = window.innerWidth < MOBILE_BREAKPOINT;
    
    /**
     * Check if current viewport is mobile
     * @returns {boolean} True if viewport width is less than mobile breakpoint
     */
    function checkMobile() {
        return window.innerWidth < MOBILE_BREAKPOINT;
    }
    
    /**
     * Create overlay element for mobile view
     * @returns {HTMLElement} The created overlay element
     */
    function createOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.addEventListener('click', closeSidebar);
        return overlay;
    }
    
    /**
     * Add overlay to DOM
     */
    function addOverlay() {
        if (!document.querySelector('.sidebar-overlay')) {
            wrapper.appendChild(createOverlay());
        }
    }
    
    /**
     * Remove overlay from DOM
     */
    function removeOverlay() {
        const overlay = document.querySelector('.sidebar-overlay');
        if (overlay) {
            overlay.removeEventListener('click', closeSidebar);
            overlay.remove();
        }
    }
    
    /**
     * Open sidebar
     */
    function openSidebar() {
        body.classList.add('sidebar-open');
        body.classList.remove('sidebar-closed');
        
        if (isMobile) {
            addOverlay();
        }
        
        saveState('open');
    }
    
    /**
     * Close sidebar
     */
    function closeSidebar() {
        body.classList.remove('sidebar-open');
        body.classList.add('sidebar-closed');
        
        if (isMobile) {
            removeOverlay();
        }
        
        saveState('closed');
    }
    
    /**
     * Toggle sidebar state
     */
    function toggleSidebar() {
        if (body.classList.contains('sidebar-open') || 
            (!body.classList.contains('sidebar-closed') && isMobile)) {
            closeSidebar();
        } else {
            openSidebar();
        }
    }
    
    /**
     * Save sidebar state to localStorage
     * @param {string} state - 'open' or 'closed'
     */
    function saveState(state) {
        localStorage.setItem(STORAGE_KEY, state);
    }
    
    /**
     * Load and apply sidebar state from localStorage
     */
    function loadState() {
        const state = localStorage.getItem(STORAGE_KEY);
        
        // Default state: open on desktop, closed on mobile
        if (!state) {
            if (isMobile) {
                closeSidebar();
            } else {
                openSidebar();
            }
            return;
        }
        
        if (state === 'open') {
            openSidebar();
        } else {
            closeSidebar();
        }
    }
    
    /**
     * Handle window resize events
     */
    function handleResize() {
        const wasMobile = isMobile;
        isMobile = checkMobile();
        
        // If changing between mobile/desktop modes
        if (wasMobile !== isMobile) {
            if (isMobile) {
                // Switching to mobile
                if (body.classList.contains('sidebar-open')) {
                    addOverlay();
                }
            } else {
                // Switching to desktop
                removeOverlay();
            }
        }
    }
    
    // Initialize event listeners
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            toggleSidebar();
        });
    });
    
    // Handle window resize
    window.addEventListener('resize', handleResize);
    
    // Initialize sidebar state
    isMobile = checkMobile();
    loadState();
    
    // Add touch swipe support for mobile
    let touchStartX = 0;
    let touchEndX = 0;
    
    document.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
    
    document.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, { passive: true });
    
    function handleSwipe() {
        const swipeThreshold = 70; // Minimum distance for swipe
        const swipeDistance = touchEndX - touchStartX;
        
        // Right swipe (open sidebar)
        if (swipeDistance > swipeThreshold && isMobile && !body.classList.contains('sidebar-open')) {
            openSidebar();
        }
        
        // Left swipe (close sidebar)
        if (swipeDistance < -swipeThreshold && isMobile && body.classList.contains('sidebar-open')) {
            closeSidebar();
        }
    }
    
    console.log('Sidebar toggle system initialized');
});

