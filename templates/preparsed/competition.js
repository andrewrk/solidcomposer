{% load jst %}
var template_status = "{% filter jst_escape %}{% include 'arena/compo_status.jst.html' %}{% endfilter %}";
var template_info = "{% filter jst_escape %}{% include 'arena/compo_info.jst.html' %}{% endfilter %}";
var template_vote_status = "{% filter jst_escape %}{% include 'arena/vote_status.jst.html' %}{% endfilter %}";
var template_entries = "{% filter jst_escape %}{% include 'arena/entry_list.jst.html' %}{% endfilter %}";
var template_current_entry = "{% filter jst_escape %}{% include 'arena/current_entry.jst.html' %}{% endfilter %}";

// pre-compiled templates
var template_status_s = null;
var template_info_s = null;
var template_vote_status_s = null;
var template_entries_s = null;
var template_current_entry_s = null;

var state_compo = null;
var resubmitting = false;
var playback_current_track = {
    index: -1,
    entry: null,
};
// states:
// 0 - waiting for compo to start
// 1 - waiting for submission deadline
// 2 - waiting for listening party start
// 3 - ongoing listening party
// 4 - voting
// 5 - competition closed
var current_state = null;

// figure out what state we're on based on dates and state_compo
function getCurrentState() {
    if (secondsUntil(state_compo.compo.start_date) > 0) {
        return 0;
    } else if (secondsUntil(state_compo.compo.submit_deadline) > 0) {
        return 1;
    }
    if (state_compo.compo.have_listening_party) {
        if (secondsUntil(state_compo.compo.listening_party_start_date) > 0) {
            return 2;
        } else if (secondsUntil(state_compo.compo.listening_party_end_date) > 0) {
            return 3;
        }
    }
    if (secondsUntil(state_compo.compo.vote_deadline) > 0) {
        return 4;
    } else {
        return 5;
    }
}

// if we're not playing any song, and we should be,
// skip to where we should be and play.
// if we're not playing any song but will be soon,
// pre-load it.
function checkIfShouldPlaySong() {
    if (ongoingListeningParty(state_compo.compo)) {
        // figure out what currently playing song should be
        var jp = $("#jplayer");
        if (! jp.jPlayer("getData", "diag.isPlaying")) {
            var current_url = MEDIA_URL+state_compo.party.entry.song.mp3_file;
            if (jp.jPlayer("getData", "diag.src") != current_url) {
                // pre-load
                jp.jPlayer("setFile", current_url);
                jp.jPlayer("play");
                // the onProgress handler will pause it when it starts playing.
            }
            if (state_compo.party.track_position >= 0) {
                jp.jPlayer("playHeadTime", state_compo.party.track_position*1000);
                jp.jPlayer("play");
            }
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
        pos += state_compo.party.buffer_time;
        last_start = pos;
        pos += state_compo.entries[i].song.length;
        ++i;
    }
    state_compo.party.index = i-1;
    state_compo.party.entry = state_compo.entries[i-1];
    state_compo.party.track_position = position - last_start;
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

function compoClosed(compo) {
    return secondsSince(compo.vote_deadline) > 0;
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

function updateEntryArea() {
    if (state_compo == null)
        return;

    $("#entry-area").html(Jst.evaluate(template_entries_s, state_compo));

    // clicks for entry-area
    $("#resubmit").click(function(){
        resubmitting = ! resubmitting;
        $("#entry-title").attr('value', state_compo.user_entry.title);
        $("#entry-comments").attr('value', state_compo.user_entry.comments);
        updateCompo();
        return false;
    });

    for (var i=0; i<state_compo.entries.length; ++i) {
        $("#entry-"+i).attr('entry_index', i);
        $("#entry-"+i).click(function(){
            var index = $(this).attr('entry_index');
            playback_current_track.index = index;
            playback_current_track.entry = state_compo.entries[index];
            playback_current_track.track_position = 0;
            $("#jplayer").jPlayer("setFile",
                MEDIA_URL+playback_current_track.entry.song.mp3_file);
            $("#jplayer").jPlayer("play");
            updateCurrentEntry();
            return false;
        });
        var vote_link = $("#vote-"+i);
        if (vote_link) {
            vote_link.attr('entry_index', i);
            vote_link.click(function(){
                var index = $(this).attr('entry_index');
                var entry = state_compo.entries[index];
                $.getJSON("/arena/ajax/vote/" + entry.id + "/", function(data){
                    ajaxRequest();
                });
                return false;
            });
        }
        var unvote_link = $("#unvote-"+i);
        if (unvote_link) {
            unvote_link.attr('entry_index', i);
            unvote_link.click(function(){
                var index = $(this).attr('entry_index');
                var entry = state_compo.entries[index];
                $.getJSON("/arena/ajax/unvote/" + entry.id + "/",function(data){
                    ajaxRequest();
                });
                return false;
            });
        }
    }
}

function updateCompo() {
    if (state_compo == null)
        return;

    updateStatus();
    updateCurrentEntry();
    $("#vote-status").html(Jst.evaluate(template_vote_status_s, state_compo));
    $("#info").html(Jst.evaluate(template_info_s, state_compo));
    updateEntryArea();

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

        current_state = getCurrentState();
        if (ongoingListeningParty(state_compo.compo))
            computeListeningPartyState();
        if (votingActive(state_compo.compo) &&
            state_compo.user.is_authenticated)
        {
            for (var i=0; i<state_compo.votes.used.length; ++i) {
                for (var j=0; j<state_compo.entries.length; ++j) {
                    if (state_compo.entries[j].id === state_compo.votes.used[i].entry)
                    {
                        state_compo.entries[j].voted_for = true;
                        break;
                    }
                }
            }
        }
        updateCompo();
    });
}

function ajaxRequestLoop() {
    ajaxRequest();
    setTimeout(ajaxRequestLoop, 10000);
}

function updateDatesLoop() {
    if (state_compo != null) {
        var new_state = getCurrentState();
        if (new_state != current_state)
            ajaxRequest();
        current_state = new_state;

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
            this.element.jPlayer("onProgressChange", function(loadPercent,
            playedPercentRelative,playedPercentAbsolute,playedTime,totalTime){
                if (ongoingListeningParty(state_compo.compo)) {
                    var current_url = MEDIA_URL+state_compo.party.entry.song.mp3_file;
                    var actually_playing = this.element.jPlayer("getData", "diag.src");
                    if (state_compo.party.track_position < 0 &&
                        current_url == actually_playing)
                    {
                        this.element.jPlayer("pause");
                    }
                } else if (votingActive(state_compo.compo) || 
                    compoClosed(state_compo.compo))
                {
                    playback_current_track.track_position = playedTime/1000;
                    updateCurrentEntry();
                }
            });
        },
        swfPath: "/static",
    });
});

