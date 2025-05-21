// Toggle actions dropdown menu
function toggleActionsMenu(button) {
  // Close all other open dropdowns first
  const allDropdowns = document.querySelectorAll('.actions-dropdown.show');
  allDropdowns.forEach(dropdown => {
    if (dropdown !== button.nextElementSibling) {
      dropdown.classList.remove('show');
    }
  });
  
  // Toggle the clicked dropdown
  const dropdown = button.nextElementSibling;
  dropdown.classList.toggle('show');
  
  // Add click outside listener to close dropdown
  document.addEventListener('click', function closeDropdown(event) {
    if (!button.contains(event.target) && !dropdown.contains(event.target)) {
      dropdown.classList.remove('show');
      document.removeEventListener('click', closeDropdown);
    }
  });
  
  // Prevent the click from propagating
  event.stopPropagation();
}
