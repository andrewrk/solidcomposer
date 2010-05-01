$(document).ready(function(){
    var dtpOptions = {
        format: "%Y-%m-%d %H:%i:%s",
        askSecond: false,
    }
    $("#id_start_date").AnyTime_picker(dtpOptions);
    $("#id_submission_deadline_date").AnyTime_picker(dtpOptions);
    $("#id_listening_party_date").AnyTime_picker(dtpOptions);

    // calculate time zone offset
    var ms = coerceDate(server_time) - local_time;
    var hours = ms / 1000 / 60 / 60;
    var offset = Math.round(hours);
    $("#id_tz_offset").attr('value', offset)
});
