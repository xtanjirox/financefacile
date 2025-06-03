document.addEventListener('DOMContentLoaded', function () {
    const sidebarToggleButtons = document.querySelectorAll('.js-sidebar-toggle');
    const body = document.body;
    const sidebar = document.getElementById('sidebar'); // Required for click-outside logic
    const STORAGE_KEY = 'sidebarIsOpen';

    // Function to check if on mobile view based on CSS breakpoint
    function isMobileView() {
        return window.innerWidth < 768;
    }

    // Apply initial state from localStorage
    function applyInitialState() {
        const storedState = localStorage.getItem(STORAGE_KEY);
        if (storedState === 'true') {
            body.classList.add('sidebar-is-open');
        } else {
            body.classList.remove('sidebar-is-open');
            // On mobile, ensure it's closed by default if no state is stored or state is 'false'
            if (isMobileView() && storedState !== 'true') {
                 body.classList.remove('sidebar-is-open');
            }
        }
    }

    applyInitialState();

    sidebarToggleButtons.forEach(button => {
        button.addEventListener('click', function (event) {
            event.preventDefault();
            event.stopPropagation(); // Prevent click from bubbling to document for click-outside logic
            const isOpen = body.classList.toggle('sidebar-is-open');
            localStorage.setItem(STORAGE_KEY, isOpen);
        });
    });

    // Close sidebar on mobile when clicking outside of it (on the overlay or main content)
    document.addEventListener('click', function (event) {
        if (isMobileView() && body.classList.contains('sidebar-is-open')) {
            // Check if the click is on the sidebar itself or the toggle button
            const isClickInsideSidebar = sidebar && sidebar.contains(event.target);
            const isClickOnToggleButton = Array.from(sidebarToggleButtons).some(btn => btn.contains(event.target));

            if (!isClickInsideSidebar && !isClickOnToggleButton) {
                body.classList.remove('sidebar-is-open');
                localStorage.setItem(STORAGE_KEY, 'false');
            }
        }
    });

    // Optional: Re-apply state on window resize if behavior needs to change, 
    // e.g. if mobile was open, and resize to desktop, should it remain open?
    // For now, this is simple and relies on initial load state + toggle clicks.
    // window.addEventListener('resize', applyInitialState); // Could be added if needed
    
    // Log for debugging
    console.log('Sidebar toggle initialized, initial collapsed state:', body.classList.contains('sidebar-collapsed'));
});
