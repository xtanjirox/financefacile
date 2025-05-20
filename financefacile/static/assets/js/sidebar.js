document.addEventListener('DOMContentLoaded', function() {
  // Sidebar toggle functionality
  const sidebarToggle = document.querySelector('.sidebar-toggle');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function() {
      document.body.classList.toggle('sidebar-toggled');
      
      // Save state to localStorage
      const isSidebarToggled = document.body.classList.contains('sidebar-toggled');
      localStorage.setItem('sidebar-toggled', isSidebarToggled);
    });
    
    // Check localStorage on page load
    const isSidebarToggled = localStorage.getItem('sidebar-toggled') === 'true';
    if (isSidebarToggled) {
      document.body.classList.add('sidebar-toggled');
    }
  }
  
  // Submenu toggle functionality
  const submenuItems = document.querySelectorAll('.has-submenu > .menu-link');
  submenuItems.forEach(item => {
    item.addEventListener('click', function(e) {
      e.preventDefault();
      const parent = this.parentElement;
      parent.classList.toggle('expanded');
    });
  });
});
