/*
* Main.js
*
* Base scripts to support the core functionality.
*
* */

$(document).ready(function() {
    $('#dtBasicExample').DataTable({
        //"scrollY": "60vh",
        //"scrollX": "10%",
        //"scrollCollapse": true,
        "aLengthMenu": [[ 15, 50, 100, -1 ], [ 15, 50, 100, "All" ]],
    });
    $('.dataTables_length').addClass('bs-select');
    $('#mySpinner').remove();
    //$('#infiniteLoading').remove();
});
