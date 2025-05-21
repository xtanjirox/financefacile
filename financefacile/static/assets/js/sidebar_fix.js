// Ensure sidebar is properly styled with white background
document.addEventListener('DOMContentLoaded', function() {
    // Force white background on sidebar
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.style.backgroundColor = '#ffffff';
        sidebar.style.boxShadow = 'none';
        sidebar.style.borderRight = '1px solid #f1f5f9';
        
        // Find all sidebar elements and ensure they have white background
        const sidebarContent = sidebar.querySelector('.sidebar-content');
        if (sidebarContent) {
            sidebarContent.style.backgroundColor = '#ffffff';
        }
        
        // Fix any simplebar elements
        const simplebarElements = sidebar.querySelectorAll('.simplebar-content, .simplebar-content-wrapper');
        simplebarElements.forEach(el => {
            el.style.backgroundColor = '#ffffff';
        });
        
        // Ensure active items have proper styling
        const activeItems = sidebar.querySelectorAll('.sidebar-item.active');
        activeItems.forEach(item => {
            item.style.backgroundColor = '#635AFF';
        });
        
        // Fix any other elements that might be affecting the sidebar
        const allSidebarElements = sidebar.querySelectorAll('*:not(.sidebar-item.active):not(.sidebar-item.active *)');
        allSidebarElements.forEach(el => {
            if (!el.classList.contains('sidebar-item') || !el.classList.contains('active')) {
                el.style.backgroundColor = '#635AFF';
                
            }
        });
    }
});
