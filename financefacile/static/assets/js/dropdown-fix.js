document.addEventListener('DOMContentLoaded', function() {
    // Initialize all dropdowns
    const dropdownToggleList = document.querySelectorAll('[data-bs-toggle="dropdown"]');
    
    if (typeof bootstrap !== 'undefined') {
        // If Bootstrap 5 is available, use it to initialize dropdowns
        dropdownToggleList.forEach(function(dropdownToggle) {
            new bootstrap.Dropdown(dropdownToggle);
        });
        console.log('Dropdowns initialized with Bootstrap 5');
    } else {
        // If Bootstrap is not available, add manual toggle functionality
        console.log('Bootstrap not found, adding manual dropdown functionality');
        
        dropdownToggleList.forEach(function(dropdownToggle) {
            dropdownToggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Find the dropdown menu
                const parent = this.closest('.dropdown');
                if (!parent) return;
                
                const dropdownMenu = parent.querySelector('.dropdown-menu');
                if (!dropdownMenu) return;
                
                // Toggle the show class
                dropdownMenu.classList.toggle('show');
                
                // Add click outside listener
                document.addEventListener('click', function closeDropdown(event) {
                    if (!parent.contains(event.target)) {
                        dropdownMenu.classList.remove('show');
                        document.removeEventListener('click', closeDropdown);
                    }
                });
            });
        });
        
        // Add CSS for manual dropdown
        const style = document.createElement('style');
        style.textContent = `
            .dropdown-menu.show {
                display: block !important;
                position: absolute !important;
                z-index: 1050 !important;
                top: 100% !important;
                right: 0 !important;
                margin-top: 0.125rem !important;
                box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
            }
            
            .dropdown-menu-end.show {
                right: 0 !important;
                left: auto !important;
            }
        `;
        document.head.appendChild(style);
    }
});
