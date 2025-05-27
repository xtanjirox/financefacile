function showTab(tabName) {
    // Get tab elements
    const invoicesTab = document.getElementById('invoices-tab');
    const expensesTab = document.getElementById('expenses-tab');
    const invoicesContent = document.getElementById('invoices');
    const expensesContent = document.getElementById('expenses');
    const viewAllInvoices = document.getElementById('view-all-invoices');
    const viewAllExpenses = document.getElementById('view-all-expenses');

    // Hide all tab contents
    invoicesContent.style.display = 'none';
    expensesContent.style.display = 'none';

    // Reset all tab buttons
    invoicesTab.classList.remove('btn-primary');
    invoicesTab.classList.add('btn-outline-primary');
    expensesTab.classList.remove('btn-danger');
    expensesTab.classList.add('btn-outline-danger');

    // Hide all view all buttons
    viewAllInvoices.classList.add('d-none');
    viewAllExpenses.classList.add('d-none');

    // Show the selected tab content and update button
    if (tabName === 'invoices') {
        invoicesContent.style.display = 'block';
        invoicesTab.classList.remove('btn-outline-primary');
        invoicesTab.classList.add('btn-primary');
        viewAllInvoices.classList.remove('d-none');
    } else if (tabName === 'expenses') {
        expensesContent.style.display = 'block';
        expensesTab.classList.remove('btn-outline-danger');
        expensesTab.classList.add('btn-danger');
        viewAllExpenses.classList.remove('d-none');
    }
}

// Initialize tabs on page load
document.addEventListener('DOMContentLoaded', function () {
    showTab('invoices');
});
