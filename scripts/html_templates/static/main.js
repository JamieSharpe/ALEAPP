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


/*
Set the navigation link to active from the current page.
*/
$(document).ready(function() {

    var current_artefact = $('#artefact_id').data("artefact");

    $('#sidebar_id').find('a').each(function () {

        if ($(this).data("artefact") == current_artefact)
        {
            $(this).addClass("active");
        }
    });
});
