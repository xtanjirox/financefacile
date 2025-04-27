// Shared DataTables initialization for product/invoice tables
$(document).ready(function() {
    $('.datatable').DataTable({
        paging: true,
        searching: true,
        info: false,
        lengthChange: false,
        language: {
            search: "<span style='color:#39739d;'>Search:</span>",
            emptyTable: "No data found."
        }
    });
});
