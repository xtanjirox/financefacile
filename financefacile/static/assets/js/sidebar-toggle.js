document.addEventListener('DOMContentLoaded', function() {
    // Get the sidebar toggle button and sidebar element
    const sidebarToggle = document.querySelector('.js-sidebar-toggle');
    const body = document.body;
    const sidebar = document.getElementById('sidebar');
    
    // Clear any previous sidebar state to ensure it's shown by default
    localStorage.removeItem('sidebarCollapsed');
    body.classList.remove('sidebar-collapsed');
    
    // Add click event listener to the sidebar toggle button
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Toggle the sidebar-collapsed class on the body
            body.classList.toggle('sidebar-collapsed');
            
            // Store the current state in localStorage
            const isCollapsed = body.classList.contains('sidebar-collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
            
            console.log('Sidebar toggled, collapsed:', isCollapsed);
        });
    } else {
        console.error('Sidebar toggle button not found');
    }
    
    // Close sidebar when clicking outside of it on mobile
    document.addEventListener('click', function(e) {
        const windowWidth = window.innerWidth;
        if (windowWidth < 768 && sidebar && !sidebar.contains(e.target) && 
            sidebarToggle && !sidebarToggle.contains(e.target)) {
            if (!body.classList.contains('sidebar-collapsed')) {
                body.classList.add('sidebar-collapsed');
                localStorage.setItem('sidebarCollapsed', true);
            }
        }
    });
    
    // Log for debugging
    console.log('Sidebar toggle initialized, sidebar shown by default');
});
