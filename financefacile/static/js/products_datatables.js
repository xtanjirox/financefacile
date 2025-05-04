// Simplified DataTables initialization for the products table
$(document).ready(function() {
    $('#products-table').DataTable({
        paging: true,
        searching: true,
        info: false,
        lengthChange: false,
        language: {
            search: "<span style='color:#39739d;'>Search:</span>",
            emptyTable: "No data found."
        },
        // Remove explicit column definitions to let DataTables auto-detect
        columnDefs: [
            { targets: -1, orderable: false, searchable: false } // Make the last column (Actions) not sortable or searchable
        ]
    });
});
