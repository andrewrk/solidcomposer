var SCCompo = function () {
    // private variables
    var that;
    
    // configurable stuff
    var jPlayerSwfPath = "/static";
    var stateRequestTimeout = 10000;

    // templates
    var template_status = "{% filter escapejs %}{% include 'arena/compo_status.jst.html' %}{% endfilter %}";
    var template_info = "{% filter escapejs %}{% include 'arena/compo_info.jst.html' %}{% endfilter %}";
    var template_vote_status = "{% filter escapejs %}{% include 'arena/vote_status.jst.html' %}{% endfilter %}";
    var template_entries = "{% filter escapejs %}{% include 'arena/entry_list.jst.html' %}{% endfilter %}";
    var template_current_entry = "{% filter escapejs %}{% include 'arena/current_entry.jst.html' %}{% endfilter %}";

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
            entry: null,
            load_percent: 0
        },
        activity: null,
        muted: false,
        media_url: null,
        urls: {% include "arena/urls.js" %},
        theme_shown: true,
        rules_shown: true
    };

    var jp = null;

    var ajaxForcePlayerUpdate = true;

    // return whether an element is visible or not
    function isVisible(div) {
        return ! (div.css("visibility") == "hidden" || 
                    div.css("display") == "none");
    }

    // show an element if it should be shown, hide if it should be hidden
    function displayCorrectly(div, visible) {
        var actuallyVisible = isVisible(div);
        if (visible && ! actuallyVisible) {
            div.show('fast');
        } else if(! visible && actuallyVisible) {
            div.hide('fast');
        }
    }

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
                current_url = state.media_url+state.json.party.entry.song.mp3_file;
                if (jp.jPlayer("getData", "diag.src") != current_url) {
                    // this will be pre-loaded because preload is 'auto'
                    // in the jplayer constructor.
                    jp.jPlayer("setFile", current_url);
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

    function updateJPVolume() {
        if (state.muted) {
            jp.jPlayer("volumeMin");
        } else {
            jp.jPlayer("volumeMax");
        }
    }

    // set forcePlayerUpdate to true to force the player to refresh
    // html. should only be used when it switches which song is playing.
    function updateCurrentEntry(forcePlayerUpdate) {
        if (state.json === null) {
            return;
        }

        var secondsPassed;
        var secondsTotal;
        var entryLoaded = false;

        if (that.ongoingListeningParty()) {
            secondsPassed = state.json.party.track_position;
            secondsTotal = state.json.party.entry.song.length;
            entryLoaded = true;
        } else if (state.current_track.entry) {
            secondsPassed = state.current_track.track_position;
            secondsTotal = state.current_track.entry.song.length;
            entryLoaded = true;
        }
        
        // only overwrite the div if it needs to.
        if (forcePlayerUpdate) {
            $("#current-entry").html(Jst.evaluate(template_current_entry_s, state));
            // clicks
            $(".player-large .button a").click(function(){
                return false;
            });
        }

        // update time and stuff
        var percent;
        var seekWidth; // pixels
        var seekMaxWidth = 800;
        if (entryLoaded) {
            // time display
            if (secondsPassed < 0) {
                $(".player-large .time").html("Buffering... " +
                    (-Math.ceil(secondsPassed)) + "s");
                percent = 0;
            } else {
                $(".player-large .time").html(Time.timeDisplay(secondsPassed)
                    + " / " + Time.timeDisplay(secondsTotal));
                percent = secondsPassed / secondsTotal;
            }

            // seek head
            seekWidth = percent * seekMaxWidth;
            waveWidth = state.current_track.load_percent * seekMaxWidth;
            $(".player-large .overlay-border").css('width', seekWidth+"px");
            $(".player-large .wave").css('width', waveWidth+"px");
        }
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
            $.getJSON(state.urls.ajax_vote(entry.id), function(data){
                that.ajaxRequest();
            });
            return false;
        }

        function entry_unvote() {
            var index;
            var entry;

            index = $(this).attr('entry_index');
            entry = state.json.entries[index];
            $.getJSON(state.urls.ajax_unvote(entry.id),function(data){
                that.ajaxRequest();
            });
            return false;
        }

        function entry_play() {
            var index;
            var entry;

            // only play if it's the right time
            if (that.votingActive() || that.compoClosed()) {
                index = $(this).attr('entry_index');
                state.current_track.index = index;
                state.current_track.entry = state.json.entries[index];
                state.current_track.track_position = 0;
                jp.jPlayer("setFile",
                    state.media_url+state.current_track.entry.song.mp3_file);
                jp.jPlayer("play");
                updateCurrentEntry(true);
                updateEntryArea();
            }

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

    function updateCompoInfo() {
        $("#info").html(Jst.evaluate(template_info_s, state));

        // show/hide theme/rules
        displayCorrectly($("#theme p"), state.theme_shown);
        $("#theme .showhide a").click(function() {
            state.theme_shown = !state.theme_shown;
            updateCompoInfo();
            return false;
        });

        displayCorrectly($("#rules p"), state.rules_shown);
        $("#rules .showhide a").click(function() {
            state.rules_shown = !state.rules_shown;
            updateCompoInfo();
            return false;
        });
    }
    
    function updateCompo() {
        var show_submission_form;
        
        if (state.json === null) {
            return;
        }

        updateStatus();

        updateCurrentEntry(ajaxForcePlayerUpdate);
        ajaxForcePlayerUpdate = false;

        $("#vote-status").html(Jst.evaluate(template_vote_status_s, state));
        updateCompoInfo();
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
                ajaxForcePlayerUpdate = true;
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

    function clearForm(form_selector) {
        $(':input',form_selector)
            .not(':button, :submit, :reset, :hidden')
            .val('')
            .removeAttr('checked')
            .removeAttr('selected');
    }

    function initializeJPlayer() {
        var current_url;
        var actually_playing;
        
        jp = $("#jplayer");
        jp.jPlayer({
            ready: function(){
                updateJPVolume();
                checkIfShouldPlaySong();
                this.element.jPlayer("onSoundComplete", function(){
                    checkIfShouldPlaySong();
                });
                this.element.jPlayer("onProgressChange",
                    function(loadPercent,playedPercentRelative,
                    playedPercentAbsolute,playedTime,totalTime)
                {
                    state.current_track.track_position = playedTime/1000;
                    state.current_track.load_percent = loadPercent/100;
                    if (that.ongoingListeningParty()) {
                        current_url = state.media_url+state.json.party.entry.song.mp3_file;
                        actually_playing = this.element.jPlayer("getData", "diag.src");
                        if (state.json.party.track_position < 0 &&
                            current_url === actually_playing)
                        {
                            this.element.jPlayer("pause");
                        }
                    }
                    updateCurrentEntry();
                });
            },
            swfPath: jPlayerSwfPath,
            preload: 'auto'
        });
    }

    that = {
        initialize: function (media_url) {
            state.media_url = media_url;
            initializeJPlayer();
            compileTemplates();
            ajaxRequestLoop();
            updateDatesLoop();
        },

        // true if we are in the middle of a listening party
        ongoingListeningParty: function () {
            if (state.json === null) {
                return false;
            }
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
            if (result.success === true) {
                state.resubmitting = false;
                // clear form
                clearForm("#submission-form");
            } else {
                alert("Unable to submit:\n\n" + result.reason);
            }
            that.ajaxRequest();
        },

        ajaxRequest: function () {
            $.getJSON(state.urls.ajax_compo(competition_id), function(data){
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

    SCCompo.initialize(MEDIA_URL);
});

