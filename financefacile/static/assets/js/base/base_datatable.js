document.addEventListener("DOMContentLoaded", function () {
    // Datatables Orders
    $("#datatables-orders").DataTable({
        responsive: true,
        aoColumnDefs: [{
            bSortable: false,
            aTargets: [-1]
        }]
    });
});