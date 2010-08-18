SCRegister = function() {
    var that;

    function refreshUi() {
        var id = $('#id_plan').val();

        if (id == 0) {
            // free plan, show the free ui
            $('.ui-free').show();
            $('.ui-paid').hide();
        } else {
            // paid plan, show the amazon button
            $('.ui-free').hide();
            $('.ui-paid').show();
        }
    }

    that = {
        initialize: function() {
            $('#id_plan').change(refreshUi);
            refreshUi();
        }
    };
    return that;
}();
$(document).ready(SCRegister.initialize);
