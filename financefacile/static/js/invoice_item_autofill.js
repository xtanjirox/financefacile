// Autofill selling price and total for invoice items
// Requires: window.PRODUCT_PRICES = {product_id: selling_price, ...}
document.addEventListener('DOMContentLoaded', function() {
    function updateRowTotal(row) {
        const qtyInput = row.querySelector('input[name$="quantity"]');
        const priceInput = row.querySelector('input[name$="selling_price"]');
        const totalInput = row.querySelector('.invoice-total-input');
        if (qtyInput && priceInput && totalInput) {
            const qty = parseFloat(qtyInput.value) || 0;
            const price = parseFloat(priceInput.value) || 0;
            totalInput.value = (qty * price).toFixed(2);
        }
    }

    function updateInvoiceTotalInput() {
        let sum = 0;
        document.querySelectorAll('.invoice-total-input').forEach(function(input) {
            sum += parseFloat(input.value) || 0;
        });
        const invoiceTotalInput = document.querySelector('.invoice-grand-total');
        if (invoiceTotalInput && !invoiceTotalInput.dataset.manual) {
            invoiceTotalInput.value = sum.toFixed(2);
        }
    }

    // Watch for manual override
    const invoiceTotalInput = document.querySelector('.invoice-grand-total');
    if (invoiceTotalInput) {
        invoiceTotalInput.addEventListener('input', function() {
            this.dataset.manual = 'true';
        });
    }

    function hookRowEvents(row) {
        const productSelect = row.querySelector('select[name$="product"]');
        const priceInput = row.querySelector('input[name$="selling_price"]');
        const qtyInput = row.querySelector('input[name$="quantity"]');
        const totalInput = row.querySelector('.invoice-total-input');
        if (productSelect && priceInput) {
            productSelect.addEventListener('change', function() {
                const pid = this.value;
                if (window.PRODUCT_PRICES && window.PRODUCT_PRICES[pid] !== undefined) {
                    priceInput.value = window.PRODUCT_PRICES[pid];
                    updateRowTotal(row);
                    updateInvoiceTotalInput();
                }
            });
        }
        if (qtyInput && priceInput && totalInput) {
            qtyInput.addEventListener('input', function() { updateRowTotal(row); updateInvoiceTotalInput(); });
            priceInput.addEventListener('input', function() { updateRowTotal(row); updateInvoiceTotalInput(); });
            totalInput.addEventListener('input', function() { updateInvoiceTotalInput(); });
        }
    }

    document.querySelectorAll('#invoice-items-body tr.item-form').forEach(hookRowEvents);

    // For dynamically added rows
    document.getElementById('add-item').addEventListener('click', function() {
        setTimeout(function() {
            document.querySelectorAll('#invoice-items-body tr.item-form').forEach(hookRowEvents);
            updateInvoiceTotalInput();
        }, 200);
    });

    // Initial total calculation
    updateInvoiceTotalInput();
});
