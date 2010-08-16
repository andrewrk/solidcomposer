var SCAccountPlan = function() {
    var that;

    function addClicks() {
        $("#reset-button").click(function(){
            // go through and reset each text box
            $(".amt-donated").each(function(index, item){
                $(item).val($(item).attr('data-init-amt'));
                var member_id = $(item).attr('data-member-id');
                $("#member-" + member_id + "-amt").val($(item).val());
            })
        })
        $(".amt-donated").change(function(){
            var member_id = $(this).attr('data-member-id');
            $("#member-" + member_id + "-amt").val($(this).val());
        })
    }

    that = {
        initialize: function() {
            addClicks();
        }
    };
    return that;
}();

$(document).ready(SCAccountPlan.initialize);
