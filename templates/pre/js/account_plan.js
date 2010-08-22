var SCAccountPlan = function() {
    var that;

    var meter_template = "{% filter escapejs %}{% include 'workbench/spacemeter.jst.html' %}{% endfilter %}";

    var user_data = null;
    var membership_data = null;

    var new_space_used = null;
    // member id: new space donated
    var new_member_space_donated = {};

    // index members by id
    var members = {};

    function compileTemplates() {
        meter_template = Jst.compile(meter_template);
    }

    function updateUi() {
        // user space meter
        $("#user-spacemeter").html(Jst.evaluate(meter_template, {
            numerator: new_space_used,
            denominator: user_data.purchased_bytes,
            number_formatter_func: Time.fileSizeFormat
        }));

        // user band count
        $("#band-count-meter").html(Jst.evaluate(meter_template, {
            numerator: user_data.bands_in_count,
            denominator: user_data.band_count_limit,
            number_formatter_func: function(x) { return x; }
        }));
        
        // for each band
        $.each(membership_data, function(index, member) {
            // used space meter
            $("#band-spacemeter-"+member.id).html(Jst.evaluate(meter_template, {
                numerator: member.band.used_space,
                denominator: member.band.total_space + (new_member_space_donated[member.id] - member.space_donated),
                number_formatter_func: Time.fileSizeFormat
            }));
            // amount donated slider max/min
            $("#amt-donated-"+member.id).slider('option', 'value', new_member_space_donated[member.id] / user_data.purchased_bytes * 100);
        });

    }

    function calculateNewSpaceUsed() {
        var sum = 0;
        $.each(membership_data, function(index, member) {
            sum += new_member_space_donated[member.id];
        });
        return sum;
    }

    function reset() {
        new_space_used = user_data.space_used;
        $.each(membership_data, function(index, member) {
            members[member.id] = member;
            new_member_space_donated[member.id] = member.space_donated;
        });
        updateUi();
    }

    function addClicks() {
        // create sliders
        $.each(membership_data, function(index, member) {
            $("#amt-donated-"+member.id).slider({
                min: 0,
                slide: function(event, ui) {
                    new_member_space_donated[member.id] = ui.value / 100.0 * user_data.purchased_bytes;
                    new_space_used = calculateNewSpaceUsed();
                    if (new_space_used > user_data.purchased_bytes) {
                        new_member_space_donated[member.id] -= (new_space_used - user_data.purchased_bytes);
                        new_space_used = user_data.purchased_bytes;
                    }
                    $("#member-" + member.id + "-amt").val(Math.round(new_member_space_donated[member.id]));
                    updateUi();
                }
            });
        });

        // hook up reset button
        $("#reset-button").click(reset);
        $(".amt-donated").change(function(){
            var member_id = $(this).attr('data-member-id');
            $("#member-" + member_id + "-amt").val($(this).val());
        })
    }

    that = {
        initialize: function(_user_data, _membership_data) {
            user_data = _user_data;
            membership_data = _membership_data;
            compileTemplates();

            addClicks();

            reset();
        }
    };
    return that;
}();

$(document).ready(function() {
    SCAccountPlan.initialize(user_data, membership_data);
});
