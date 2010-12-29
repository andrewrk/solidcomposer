/*
 * Dependencies:
 *  Time
 *  jQuery
 *
 */

var SCCreateCompo = function () {
    var that;

    // return whether an element is visible or not
    function isVisible(div) {
        return ! (div.css("visibility") == "hidden" || 
                    div.css("display") == "none");
    }

    function displayCorrectly(div, visible) {
        var actuallyVisible = isVisible(div);
        if (visible && ! actuallyVisible) {
            div.show();
        } else if(! visible && actuallyVisible) {
            div.hide();
        }
    }


    that = {
        displayCorrectInputs: function () {
            var have_theme;
            var have_rules;
            var have_lp;
            var immediately;

            // hide theme box and preview theme if have theme is unchecked
            have_theme = Boolean($("#id_have_theme").attr('checked'));
            displayCorrectly($("#div_theme"), have_theme);
            displayCorrectly($("#div_preview_theme"), have_theme);
            
            // hide rule box and preview rules if have rules is unchecked
            have_rules = Boolean($("#id_have_rules").attr('checked'));
            displayCorrectly($("#div_rules"), have_rules);
            displayCorrectly($("#div_preview_rules"), have_rules);

            // hide immediately and lp date if have lp is unchecked
            have_lp = Boolean($("#id_have_listening_party").attr('checked'));
            displayCorrectly($("#div_immediately"), have_lp);
            // hide lp date if immediately is checked
            immediately = Boolean($("#id_party_immediately").attr('checked'));
            displayCorrectly($("#div_lp_date"), ! immediately && have_lp);
        }
    };
    return that;
} ();

$(document).ready(function(){
    var dtpOptions = {
        format: "%Y-%m-%d %H:%i:%s"
    };

    // calculate time zone offset
    var ms = Time.coerceDate(server_time) - local_time;
    var hours = ms / 1000 / 60 / 60;
    var offset = Math.round(hours);
    $("#id_tz_offset").attr('value', offset);

    var start_date_box = $("#id_start_date");
    var submission_deadline_box = $("#id_submission_deadline_date");
    var listening_party_date_box = $("#id_listening_party_date");
    
    // correct date text boxes for tz offset if they have values
    var start_date_val = start_date_box.val();
    var submission_deadline_val = submission_deadline_box.val();
    var listening_party_date_val = listening_party_date_box.val();

    if (start_date_val.length > 0) {
        start_date_box.val(Time.toDjangoDate(Time.localTime(Time.fromDjangoDate(start_date_val))));
    }
    if (submission_deadline_val.length > 0) {
        submission_deadline_box.val(Time.toDjangoDate(Time.localTime(Time.fromDjangoDate(submission_deadline_val))));
    }
    if (listening_party_date_val.length > 0) {
        listening_party_date_box.val(Time.toDjangoDate(Time.localTime(Time.fromDjangoDate(listening_party_date_val))));
    }

    // use the any time picker ui
    start_date_box.AnyTime_picker(dtpOptions);
    submission_deadline_box.AnyTime_picker(dtpOptions);
    listening_party_date_box.AnyTime_picker(dtpOptions);

    // show/hide ui elements
    SCCreateCompo.displayCorrectInputs();

    $("#id_have_theme").change(SCCreateCompo.displayCorrectInputs);
    $("#id_have_rules").change(SCCreateCompo.displayCorrectInputs);
    $("#id_have_listening_party").change(SCCreateCompo.displayCorrectInputs);
    $("#id_party_immediately").change(SCCreateCompo.displayCorrectInputs);
});
