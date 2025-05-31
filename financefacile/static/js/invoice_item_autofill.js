// Autofill selling price and total for invoice items
// Requires: window.PRODUCT_PRICES = {product_id: selling_price, ...}
document.addEventListener('DOMContentLoaded', function() {
    console.log('Invoice item autofill script loaded');
    console.log('Product prices available:', window.PRODUCT_PRICES);
    
    // Initialize Select2 for all product dropdowns
    $('.select2').select2({
        width: '100%',
        dropdownCssClass: 'select2-dropdown-modern',
        theme: 'classic'
    });
    
    function updateRowTotal(row) {
        const qtyInput = row.querySelector('input.item-quantity');
        const priceInput = row.querySelector('input.item-price');
        const totalInput = row.querySelector('input.item-total');
        
        if (qtyInput && priceInput && totalInput) {
            const qty = parseFloat(qtyInput.value) || 0;
            const price = parseFloat(priceInput.value) || 0;
            const total = qty * price;
            totalInput.value = total.toFixed(2);
            console.log(`Updated row total: ${qty} × ${price} = ${total.toFixed(2)}`);
        }
    }

    function updateInvoiceTotalInput() {
        let sum = 0;
        document.querySelectorAll('input.item-total').forEach(function(input) {
            sum += parseFloat(input.value) || 0;
        });
        
        const invoiceTotalInput = document.querySelector('.invoice-grand-total');
        if (invoiceTotalInput && !invoiceTotalInput.dataset.manual) {
            invoiceTotalInput.value = sum.toFixed(2);
            console.log(`Updated invoice total: ${sum.toFixed(2)}`);
        }
    }

    // Watch for manual override of the invoice total
    const invoiceTotalInput = document.querySelector('.invoice-grand-total');
    if (invoiceTotalInput) {
        invoiceTotalInput.addEventListener('input', function() {
            this.dataset.manual = 'true';
            console.log('Manual override of invoice total');
        });
    }

    // Function to handle product selection and update price
    function handleProductSelection(select, row) {
        const productId = select.value;
        const priceInput = row.querySelector('input.item-price');
        
        console.log(`Product selected: ID=${productId}`);
        
        if (productId && window.PRODUCT_PRICES && window.PRODUCT_PRICES[productId] !== undefined) {
            const price = window.PRODUCT_PRICES[productId];
            priceInput.value = price;
            console.log(`Setting price to ${price} for product ID ${productId}`);
            
            // Update totals
            updateRowTotal(row);
            updateInvoiceTotalInput();
        } else {
            console.log(`No price found for product ID ${productId}`);
        }
    }

    // Function to attach event handlers to a row
    function setupRow(row) {
        const select = row.querySelector('select');
        const qtyInput = row.querySelector('input.item-quantity');
        const priceInput = row.querySelector('input.item-price');
        
        if (select) {
            // Handle both the Select2 event and the native change event
            $(select).on('select2:select', function(e) {
                handleProductSelection(select, row);
            });
            
            select.addEventListener('change', function() {
                handleProductSelection(select, row);
            });
            
            // If a product is already selected, set the price
            if (select.value) {
                handleProductSelection(select, row);
            }
        }
        
        if (qtyInput) {
            qtyInput.addEventListener('input', function() {
                updateRowTotal(row);
                updateInvoiceTotalInput();
            });
        }
        
        if (priceInput) {
            priceInput.addEventListener('input', function() {
                updateRowTotal(row);
                updateInvoiceTotalInput();
            });
        }
    }

    // Setup all existing rows
    document.querySelectorAll('#invoice-items-body tr.item-form').forEach(function(row) {
        setupRow(row);
        updateRowTotal(row);
    });

    // Setup handler for adding new rows
    const addButton = document.getElementById('add-item');
    if (addButton) {
        addButton.addEventListener('click', function() {
            console.log('Add item button clicked');
            
            // Wait for the DOM to update with the new row
            setTimeout(function() {
                const rows = document.querySelectorAll('#invoice-items-body tr.item-form');
                const newRow = rows[rows.length - 1];
                
                if (newRow) {
                    // Initialize Select2 for the new row
                    $(newRow).find('select').select2({
                        width: '100%',
                        dropdownCssClass: 'select2-dropdown-modern',
                        theme: 'classic'
                    });
                    
                    setupRow(newRow);
                    console.log('New row setup complete');
                }
                
                updateInvoiceTotalInput();
            }, 200);
        });
    }

    // Calculate initial totals
    updateInvoiceTotalInput();
    console.log('Invoice item autofill initialization complete');
});
