var template_status = (<r><![CDATA[{% include 'arena/compo_status.jst.html' %}]]></r>).toString();
var template_info = (<r><![CDATA[{% include 'arena/compo_info.jst.html' %}]]></r>).toString();
var template_vote_status = (<r><![CDATA[{% include 'arena/vote_status.jst.html' %}]]></r>).toString();
var template_entries = (<r><![CDATA[{% include 'arena/entry_list.jst.html' %}]]></r>).toString();
var template_current_entry = (<r><![CDATA[{% include 'arena/current_entry.jst.html' %}]]></r>).toString();

// pre-compiled templates
var template_status_s = null;
var template_info_s = null;
var template_vote_status_s = null;
var template_entries_s = null;
var template_current_entry_s = null;

var state_compo = null;


// functions called when submitting upload entry form.
function submitEntryStartCallback() {

}

function submitEntryCompleteCallback(response) {
    if (response.indexOf('<pre>') === 0)
        response = response.substr(5, response.length-'<pre>'.length-'</pre>'.length);
    
    result = eval('(' + response + ')');
    if (result.success == false) {
        alert("Unable to submit:\n\n" + result.reason);
    }
}

// true if we are in the middle of a listening party
function ongoingListeningParty(compo) {
    return compo != null && secondsUntil(compo.vote_deadline) > 0 &&
    ((compo.have_listening_party &&
        secondsUntil(compo.listening_party_end_date) <= 0) ||
        ! compo.have_listening_party);
}

function updateStatus() {
    if (state_compo == null)
        return;

    $("#status").html(Jst.evaluateCompiled(template_status_s, state_compo));
}

function updateCompo() {
    if (state_compo == null)
        return;

    updateStatus();
    $("#vote-status").html(Jst.evaluateCompiled(template_vote_status_s, state_compo));
    $("#info").html(Jst.evaluateCompiled(template_info_s, state_compo));
    $("#entry-area").html(Jst.evaluateCompiled(template_entries_s, state_compo));
    $("#current-entry").html(Jst.evaluateCompiled(template_current_entry_s, state_compo));

    var show_submission_form =
        secondsUntil(state_compo.compo.submit_deadline) > 0 &&
        secondsUntil(state_compo.compo.start_date) < 0;
    if (show_submission_form)
        $("#submission").show('fast');
    else
        $("#submission").hide('fast');
}

function ajaxRequest() {
    $.getJSON("/arena/ajax/compo/" + competition_id + "/", function(data){
        if (data == null)
            return;

        state_compo = data;

        updateCompo();
    });
}

function ajaxRequestLoop() {
    ajaxRequest();
    setTimeout(ajaxRequestLoop, 10000);
}

function updateDatesLoop() {
    updateStatus();
    setTimeout(updateDatesLoop, 1000);
}

function compileTemplates() {
    template_status_s = Jst.compile(template_status);
    template_info_s = Jst.compile(template_info);
    template_vote_status_s = Jst.compile(template_vote_status);
    template_entries_s = Jst.compile(template_entries);
    template_onliners_s = Jst.compile(template_onliners);
    template_current_entry_s = Jst.compile(template_current_entry);
}

$(document).ready(function(){
    compileTemplates();
    ajaxRequestLoop();
    updateDatesLoop();
    chatInitialize();
    loginInitialize();
});

