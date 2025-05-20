// Sidebar toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get the sidebar toggle button
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    
    // Add click event listener to the toggle button
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            // Toggle the sidebar-toggled class on the body
            document.body.classList.toggle('sidebar-toggled');
            
            // Store the sidebar state in localStorage
            const isSidebarToggled = document.body.classList.contains('sidebar-toggled');
            localStorage.setItem('sidebar-toggled', isSidebarToggled);
        });
        
        // Check if sidebar state is stored in localStorage
        const isSidebarToggled = localStorage.getItem('sidebar-toggled') === 'true';
        if (isSidebarToggled) {
            document.body.classList.add('sidebar-toggled');
        }
    }
});
