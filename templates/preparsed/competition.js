{% load jst %}

var SCCompo = function () {
    // private variables
    var that;
    
    // configurable stuff
    var jPlayerSwfPath = "/static";
    var stateRequestTimeout = 10000;

    // templates
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

    var activity_enum = {
        waitUntilStart: 0,
        waitUntilDeadline: 1,
        waitForLPStart: 2,
        ongoingLP: 3,
        voting: 4,
        closed: 5
    };

    var state = {
        json: null,
        resubmitting: false,
        current_track: {
            index: -1,
            entry: null
        },
        activity: null
    };

    var jp = null;

    // figure out what state we're on based on dates and state.json
    function getCurrentActivity() {
        if (Time.secondsUntil(state.json.compo.start_date) > 0) {
            return activity_enum.waitUntilStart;
        } else if (Time.secondsUntil(state.json.compo.submit_deadline) > 0) {
            return activity_enum.waitUntilDeadline;
        }
        if (state.json.compo.have_listening_party) {
            if (Time.secondsUntil(state.json.compo.listening_party_start_date) > 0) {
                return activity_enum.waitForLPStart;
            } else if (Time.secondsUntil(state.json.compo.listening_party_end_date) > 0) {
                return activity_enum.ongoingLP;
            }
        }
        if (Time.secondsUntil(state.json.compo.vote_deadline) > 0) {
            return activity_enum.voting;
        } else {
            return activity_enum.closed;
        }
    }
    
    // if we're not playing any song, and we should be,
    // skip to where we should be and play.
    // if we're not playing any song but will be soon,
    // pre-load it.
    function checkIfShouldPlaySong() {
        var current_url;
        
        if (that.ongoingListeningParty()) {
            // figure out what currently playing song should be
            if (! jp.jPlayer("getData", "diag.isPlaying")) {
                current_url = MEDIA_URL+state.json.party.entry.song.mp3_file;
                if (jp.jPlayer("getData", "diag.src") != current_url) {
                    // pre-load
                    jp.jPlayer("setFile", current_url).jPlayer("play").jPlayer("stop");
                }
                if (state.json.party.track_position >= 0) {
                    jp.jPlayer("playHeadTime", state.json.party.track_position*1000);
                    jp.jPlayer("play");
                }
            }
        }
    }

    function computeListeningPartyState() {
        var position = Time.secondsSince(state.json.compo.listening_party_start_date);
        var i = 0;
        var pos = 0;
        var last_start = 0;
        while (pos < position && i < state.json.entries.length) {
            pos += state.json.party.buffer_time;
            last_start = pos;
            pos += state.json.entries[i].song.length;
            ++i;
        }
        state.json.party.index = i-1;
        state.json.party.entry = state.json.entries[i-1];
        state.json.party.track_position = position - last_start;
    }

    // return the server time of when voting is allowed
    function voteStartDate(compo) {
        return compo.have_listening_party ?
            compo.listening_party_end_date :
            compo.submit_deadline;
    }

    function updateStatus() {
        if (state.json === null) {
            return;
        }
        $("#status").html(Jst.evaluate(template_status_s, state));
    }

    function updateCurrentEntry() {
        if (state.json === null) {
            return;
        }
        $("#current-entry").html(Jst.evaluate(template_current_entry_s, state));
    }

    function updateEntryArea() {
        var i;
        var play_link;
        var vote_link;
        var unvote_link;
        
        if (state.json === null) {
            return;
        }

        $("#entry-area").html(Jst.evaluate(template_entries_s, state));

        // clicks for entry-area
        $("#resubmit").click(function(){
            state.resubmitting = ! state.resubmitting;
            $("#entry-title").attr('value', state.json.user_entry.title);
            $("#entry-comments").attr('value', state.json.user_entry.comments);
            updateCompo();
            return false;
        });

        function entry_vote() {
            var index;
            var entry;

            index = $(this).attr('entry_index');
            entry = state.json.entries[index];
            $.getJSON("/arena/ajax/vote/" + entry.id + "/", function(data){
                that.ajaxRequest();
            });
            return false;
        }

        function entry_unvote() {
            var index;
            var entry;

            index = $(this).attr('entry_index');
            entry = state.json.entries[index];
            $.getJSON("/arena/ajax/unvote/" + entry.id + "/",function(data){
                that.ajaxRequest();
            });
            return false;
        }

        function entry_play() {
            var index;
            var entry;

            index = $(this).attr('entry_index');
            state.current_track.index = index;
            state.current_track.entry = state.json.entries[index];
            state.current_track.track_position = 0;
            jp.jPlayer("setFile",
                MEDIA_URL+state.current_track.entry.song.mp3_file);
            jp.jPlayer("play");
            updateCurrentEntry();
            return false;
        }

        for (i=0; i<state.json.entries.length; ++i) {
            play_link = $("#entry-"+i);
            if (play_link) {
                play_link.attr('entry_index', i);
                play_link.click(entry_play);
            }

            vote_link = $("#vote-"+i);
            if (vote_link) {
                vote_link.attr('entry_index', i);
                vote_link.click(entry_vote);
            }
            unvote_link = $("#unvote-"+i);
            if (unvote_link) {
                unvote_link.attr('entry_index', i);
                unvote_link.click(entry_unvote);
            }
        }
    }
    
    function updateCompo() {
        var show_submission_form;
        
        if (state.json === null) {
            return;
        }

        updateStatus();
        updateCurrentEntry();
        $("#vote-status").html(Jst.evaluate(template_vote_status_s, state));
        $("#info").html(Jst.evaluate(template_info_s, state));
        updateEntryArea();

        // show/hide submission form
        show_submission_form = state.json.user.is_authenticated &&
            that.submissionActive() && (! state.json.submitted || state.resubmitting);
        if (show_submission_form) {
            $("#submission").show('fast');
        } else {
            $("#submission").hide('fast');
        }
    }



    function ajaxRequestLoop() {
        that.ajaxRequest();
        setTimeout(ajaxRequestLoop, stateRequestTimeout);
    }

    function updateDatesLoop() {
        var new_activity;
        
        if (state.json !== null) {
            new_activity = getCurrentActivity();
            if (new_activity != state.activity) {
                that.ajaxRequest();
            }
            state.activity = new_activity;

            if (that.ongoingListeningParty()) {
                computeListeningPartyState();
            }

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

    function initializeJPlayer() {
        var current_url;
        var actually_playing;
        
        jp = $("#jplayer");
        jp.jPlayer({
            ready: function(){
                checkIfShouldPlaySong();
                this.element.jPlayer("onSoundComplete", function(){
                    checkIfShouldPlaySong();
                });
                this.element.jPlayer("onProgressChange",
                    function(loadPercent,playedPercentRelative,
                    playedPercentAbsolute,playedTime,totalTime)
                {
                    if (that.ongoingListeningParty()) {
                        current_url = MEDIA_URL+state.json.party.entry.song.mp3_file;
                        actually_playing = this.element.jPlayer("getData", "diag.src");
                        if (state.json.party.track_position < 0 &&
                            current_url === actually_playing)
                        {
                            this.element.jPlayer("pause");
                        }
                    } else if (that.votingActive() || 
                        that.compoClosed(state.json.compo))
                    {
                        state.current_track.track_position = playedTime/1000;
                        updateCurrentEntry();
                    }
                });
            },
            swfPath: jPlayerSwfPath
        });
    }

    that = {
        initialize: function () {
            initializeJPlayer();
            compileTemplates();
            ajaxRequestLoop();
            updateDatesLoop();
        },

        // true if we are in the middle of a listening party
        ongoingListeningParty: function () {
            var compo = state.json.compo;
            return compo !== null && compo.have_listening_party &&
                Time.secondsSince(compo.listening_party_start_date) > 0 &&
                Time.secondsUntil(compo.listening_party_end_date) > 0;
        },

        // true if people can vote right now
        votingActive: function () {
            var compo = state.json.compo;
            return Time.secondsUntil(compo.vote_deadline) > 0 &&
               Time.secondsSince(voteStartDate(compo)) > 0;
        },

        compoClosed: function () {
            var compo = state.json.compo;
            return Time.secondsSince(compo.vote_deadline) > 0;
        },

        submissionActive: function () {
            return Time.secondsUntil(state.json.compo.submit_deadline) > 0 &&
                Time.secondsSince(state.json.compo.start_date) > 0;
        },

        // functions called when submitting upload entry form.
        submitEntryStartCallback: function () {

        },

        submitEntryCompleteCallback: function (response) {
            var result;
            
            if (response.indexOf('<pre>') === 0) {
                response = response.substr(5, response.length-'<pre>'.length-'</pre>'.length);
            }
            
            result = eval('(' + response + ')');
            if (result.success === false) {
                alert("Unable to submit:\n\n" + result.reason);
            }

            state.resubmitting = false;

            that.ajaxRequest();
        },

        ajaxRequest: function () {
            $.getJSON("/arena/ajax/compo/" + competition_id + "/", function(data){
                var i;
                var j;
                
                if (data === null) {
                    return;
                }

                state.json = data;

                state.activity = getCurrentActivity();
                if (that.ongoingListeningParty()) {
                    computeListeningPartyState();
                }
                if (that.votingActive() &&
                    state.json.user.is_authenticated)
                {
                    for (i=0; i<state.json.votes.used.length; ++i) {
                        for (j=0; j<state.json.entries.length; ++j) {
                            if (state.json.entries[j].id === state.json.votes.used[i].entry)
                            {
                                state.json.entries[j].voted_for = true;
                                break;
                            }
                        }
                    }
                }
                updateCompo();
            });
        }
    };
    return that;
} ();

$(document).ready(function(){
    Time.initialize(server_time, local_time);
    Chat.initialize(chatroom_id);

    Login.initialize();
    Login.addStateChangeCallback(SCCompo.ajaxRequest);

    SCCompo.initialize();
});

