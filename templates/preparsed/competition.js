var template_status = (<r><![CDATA[{% include 'arena/compo_status.jst.html' %}]]></r>).toString();
var template_info = (<r><![CDATA[{% include 'arena/compo_info.jst.html' %}]]></r>).toString();
var template_vote_status = (<r><![CDATA[{% include 'arena/vote_status.jst.html' %}]]></r>).toString();
var template_entries = (<r><![CDATA[{% include 'arena/entry_list.jst.html' %}]]></r>).toString();

var template_chat = (<r><![CDATA[{% include 'chat/box.jst.html' %}]]></r>).toString();
var template_onliners = (<r><![CDATA[{% include 'chat/onliners.jst.html' %}]]></r>).toString();

var state_compo = null;
var state_chat = null;

var SYSTEM = 0, ACTION = 1, MESSAGE = 2, JOIN = 3, LEAVE = 4, NOTICE = 5;
var chat_last_update = null;

// true if we are in the middle of a listening party
function ongoingListeningParty(compo) {
    return compo != null && secondsUntil(compo.vote_deadline) > 0 &&
    ((compo.have_listening_party &&
        secondsUntil(compo.listening_party_end_date) <= 0) ||
        ! compo.have_listening_party);
}

function updateChat() {
    if (state_chat == null)
        return;
    
    $("#chatroom-outer-box").html(Jst.evaluate(template_chat, state_chat));
    $("#chat-say-text").keydown(function(event){
        if (event.keyCode == 13) {
            // say something in chat
            var msg_to_post = $("#chat-say-text").attr('value');
            if (msg_to_post == '')
                return;
            $("#chat-say-text").attr('value','');
            $.ajax({
                url: "/ajax/chat/say/",
                type: 'POST',
                dataType: 'text',
                data: {
                    'room': chatroom_id,
                    'message': msg_to_post,
                },
                success: function(){
                    // add the message and clear the box
                    var new_message = {
                        'room': chatroom_id,
                        'type': MESSAGE,
                        'author': state_chat.user.get_profile,
                        'message': msg_to_post,
                        'timestamp': serverTime(new Date()),
                    };
                    new_message.author.username = state_chat.user.username;
                    state_chat.messages.push(new_message);
                    updateChat();
                    
                    // set focus to this widget again
                    $("#chat-say-text").focus();
                },
                error: function(){
                    // TODO: show some kind of error message
                },
            });
        }
    });

    $("#chatroom-outer-onliners").html(Jst.evaluate(template_onliners, state_chat));
}

function updateStatus() {
    if (state_compo == null)
        return;

    $("#status").html(Jst.evaluate(template_status, state_compo));
}

function updateCompo() {
    if (state_compo == null)
        return;

    updateStatus();
    $("#vote-status").html(Jst.evaluate(template_vote_status, state_compo));
    $("#info").html(Jst.evaluate(template_info, state_compo));
    $("#entry-area").html(Jst.evaluate(template_entries, state_compo));
}

function ajaxRequest() {
    loginAjaxRequest();
    
    $.getJSON("/arena/ajax/compo/" + competition_id + "/", function(data){
        if (data == null)
            return;

        state_compo = data;

        updateCompo();
    });

    $.getJSON("/ajax/chat/",
        {
            "latest_check": chat_last_update,
            "room": chatroom_id,
        },
        function(data){
            if (data == null)
                return;

            state_chat = data;

            updateChat();
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

$(document).ready(function(){
    ajaxRequestLoop();
    updateDatesLoop();
});

