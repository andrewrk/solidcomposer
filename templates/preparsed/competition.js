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
var resubmitting = false;


// if we're not playing any song, and we should be,
// skip to where we should be and play.
// if we're not playing any song but will be soon,
// pre-load it.
function checkIfShouldPlaySong() {
    if (ongoingListeningParty(state_compo.compo)) {
        // figure out what currently playing song should be
        if (! $("#jplayer").jPlayer("getData", "diag.isPlaying")) {
            $("#jplayer").jPlayer("setFile", MEDIA_URL+state_compo.party.entry.song.mp3_file);
            $("#jplayer").jPlayer("playHeadTime", state_compo.party.track_position*1000);
            $("#jplayer").jPlayer("play");
        }
    }
}

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

    resubmitting = false;

    ajaxRequest();
}

function computeListeningPartyState() {
    var position = secondsSince(state_compo.compo.listening_party_start_date);
    var i = 0;
    var pos = 0;
    var last_start = 0;
    while (pos < position && i < state_compo.entries.length) {
        last_start = pos;
        pos += state_compo.entries[i].song.length;
        ++i;
    }
    state_compo.party = {
        index: i-1,
        entry: state_compo.entries[i-1],
        track_position: position - last_start,
    };
}

// true if we are in the middle of a listening party
function ongoingListeningParty(compo) {
    return compo != null && compo.have_listening_party &&
        secondsSince(compo.listening_party_start_date) > 0 &&
        secondsUntil(compo.listening_party_end_date) > 0;
}

// return the server time of when voting is allowed
function voteStartDate(compo) {
    return compo.have_listening_party ?
        compo.listening_party_end_date :
        compo.submit_deadline;
}

// true if people can vote right now
function votingActive(compo) {
    return secondsUntil(compo.vote_deadline) > 0 &&
       secondsSince(voteStartDate(compo)) > 0;
}

function submissionActive() {
    return secondsUntil(state_compo.compo.submit_deadline) > 0 &&
        secondsSince(state_compo.compo.start_date) > 0;
}

function updateStatus() {
    if (state_compo == null)
        return;
    $("#status").html(Jst.evaluate(template_status_s, state_compo));
}

function updateCurrentEntry() {
    if (state_compo == null)
        return;
    $("#current-entry").html(Jst.evaluate(template_current_entry_s, state_compo));
}

function updateCompo() {
    if (state_compo == null)
        return;

    updateStatus();
    updateCurrentEntry();
    $("#vote-status").html(Jst.evaluate(template_vote_status_s, state_compo));
    $("#info").html(Jst.evaluate(template_info_s, state_compo));
    $("#entry-area").html(Jst.evaluate(template_entries_s, state_compo));

    // clicks for entry-area
    $("#resubmit").click(function(){
        resubmitting = ! resubmitting;
        $("#entry-title").attr('value', state_compo.user_entry.title);
        $("#entry-comments").attr('value', state_compo.user_entry.comments);
        updateCompo();
        return false;
    });

    // show/hide submission form
    var show_submission_form = submissionActive() &&
        (! state_compo.submitted || resubmitting);
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

        if (ongoingListeningParty(state_compo.compo))
            computeListeningPartyState();
        updateCompo();
    });
}

function ajaxRequestLoop() {
    ajaxRequest();
    setTimeout(ajaxRequestLoop, 10000);
}

function updateDatesLoop() {
    if (state_compo != null) {
        if (ongoingListeningParty(state_compo.compo))
            computeListeningPartyState();

        updateStatus();
        updateCurrentEntry();
        checkIfShouldPlaySong();
    }

    setTimeout(updateDatesLoop, 1000);
}

function compileTemplates() {
    template_status_s = Jst.compile(template_status);
    template_info_s = Jst.compile(template_info);
    template_vote_status_s = Jst.compile(template_vote_status);
    template_entries_s = Jst.compile(template_entries);
    template_current_entry_s = Jst.compile(template_current_entry);
}

$(document).ready(function(){
    compileTemplates();
    ajaxRequestLoop();
    updateDatesLoop();
    chatInitialize();
    loginInitialize();

    $("#jplayer").jPlayer({
        ready: function(){
            checkIfShouldPlaySong();
            this.element.jPlayer("onSoundComplete", function(){
                checkIfShouldPlaySong();
            });
        },
        swfPath: "/static",
    });
});

