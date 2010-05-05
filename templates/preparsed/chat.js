{% load jst %}
/*
 * chat.js - include this if you have a chat room on the page.
 *
 * Dependencies:
 *  jst-parser 0.4.0 - http://github.com/superjoe30/jst-parser
 *  time.js - needs to already be initialized
 *  jQuery 1.4.2
 *
 * This class needs to be initialized on document ready:
 *
 * Chat.initialize(chatroom_id);
 *
 */

var Chat = function() {
    // private variables:
    var that; // reference to the public object

    // configurable stuff
    var messageRequestTimeout = 4000;
    var onlinersRequestTimeout = 10000;

    // jst templates
    var template_chat = "{% filter jst_escape %}{% include 'chat/box.jst.html' %}{% endfilter %}";
    var template_onliners = "{% filter jst_escape %}{% include 'chat/onliners.jst.html' %}{% endfilter %}";
    var template_cannot_say = "{% filter jst_escape %}{% include 'chat/cannot_say.jst.html' %}{% endfilter %}";
    var template_say = "{% filter jst_escape %}{% include 'chat/say.jst.html' %}{% endfilter %}";
    
    // compiled templates
    var template_chat_s = null;
    var template_onliners_s = null;
    var template_cannot_say_s = null;
    var template_say_s = null;

    var state_chat = null;
    var chat_can_say = null;

    var chat_last_update = null;
    var chat_temp_msg_count = 0;
    
    var chatroom_id;

    // private functions:
    function chatAddClicksToSay() {
        $("#chat-say-text").keydown(function(event){
            if (event.keyCode === 13) {
                // say something in chat
                var msg_to_post = $("#chat-say-text").attr('value');
                if (msg_to_post === '') {
                    return;
                }
                $("#chat-say-text").attr('value','');
                $.ajax({
                    url: "/ajax/chat/say/",
                    type: 'POST',
                    dataType: 'text',
                    data: {
                        'room': chatroom_id,
                        'message': msg_to_post
                    },
                    success: function(){
                        // add the message and clear the box
                        var new_message = {
                            'room': chatroom_id,
                            'type': that.message_type.MESSAGE,
                            'author': state_chat.user.get_profile,
                            'message': msg_to_post,
                            'timestamp': Time.serverTime(new Date())
                        };
                        new_message.author.username = state_chat.user.username;
                        state_chat.messages.push(new_message);
                        ++chat_temp_msg_count;
                        updateChat();
                        
                        // set focus to this widget again
                        $("#chat-say-text").focus();
                    },
                    error: function(){
                        // TODO: show some kind of error message
                    }
                });
                return false;
            }
        });
    }

    function updateChat() {
        var new_chat_can_say;
        var different;
        
        if (state_chat === null) {
            return;
        }
        
        new_chat_can_say = that.chatRoomActive(state_chat.room) &&
            state_chat.user.is_authenticated &&
            state_chat.user.has_permission;
        different = new_chat_can_say !== chat_can_say;
        chat_can_say = new_chat_can_say;
        if (different) {
            $("#chatroom-say").html(Jst.evaluate(template_say_s, state_chat));
            chatAddClicksToSay();
            $("#chatroom-cannot-say").html(Jst.evaluate(template_cannot_say_s, state_chat));
        }

        $("#chatroom-outer-box").html(Jst.evaluate(template_chat_s, state_chat));
        if (chat_can_say) {
            $("#chatroom-cannot-say").hide();
            $("#chatroom-say").show();
        } else {
            $("#chatroom-cannot-say").show();
            $("#chatroom-say").hide();
        }
    }

    function updateChatOnliners() {
        $("#chatroom-outer-onliners").html(Jst.evaluate(template_onliners_s, state_chat));
    }

    function chatOnlinersAjaxRequest() {
        $.getJSON("/ajax/chat/online/",
            {
                "room": chatroom_id
            },
            function(data){
                if (data === null) {
                    return;
                }

                if (state_chat === null) {
                    state_chat = {user: null, messages: []};
                }

                state_chat.onliners = data;
                updateChatOnliners();
            });
    }

    function chatAjaxRequest() {
        $.getJSON("/ajax/chat/",
            {
                "latest_check": chat_last_update,
                "room": chatroom_id
            },
            function(data){
                var container;
                var scroll;
                var i;
                
                if (data === null) {
                    return;
                }

                if (state_chat === null) {
                    state_chat = {'user': null, 'messages': []};
                }

                // clear temporary messages
                while (chat_temp_msg_count > 0) {
                    state_chat.messages.pop();
                    --chat_temp_msg_count;
                }

                // see if we're at the bottom of the div
                container = $("#chatroom-messages");
                scroll = (container.scrollTop() === container.attr('scrollHeight') - container.height());

                state_chat.room = data.room;
                state_chat.user = data.user;
                for (i=0; i<data.messages.length; ++i) {
                    state_chat.messages.push(data.messages[i]);
                }
                if (data.messages.length > 0) {
                    chat_last_update = data.messages[data.messages.length-1].timestamp;
                }

                if (that.beforeChatRoomActive(state_chat.room)) {
                    chat_last_update = null;
                }

                updateChat();

                if (scroll) {
                    $("#chatroom-messages").animate({ scrollTop: $("#chatroom-messages").attr('scrollHeight')}, 500);
                }
            });
    }

    function chatAjaxRequestLoop() {
        chatAjaxRequest();
        setTimeout(chatAjaxRequestLoop, messageRequestTimeout);
    }

    function chatOnlinersAjaxRequestLoop() {
        chatOnlinersAjaxRequest();
        setTimeout(chatOnlinersAjaxRequest, onlinersRequestTimeout);
    }

    function chatCompileTemplates() {
        template_chat_s = Jst.compile(template_chat);
        template_onliners_s = Jst.compile(template_onliners);
        template_cannot_say_s = Jst.compile(template_cannot_say);
        template_say_s = Jst.compile(template_say);
    }

    that = {
        // public variables:
        message_type: {
            SYSTEM: 0,
            ACTION: 1,
            MESSAGE:2,
            JOIN:   3,
            LEAVE:  4,
            NOTICE: 5
        },

        // public functions:
        chatRoomActive: function (room) {
            var now = new Date();
            var local;

            if (room.start_date !== null) {
                local = Time.localTime(room.start_date);
                if (local > now) {
                    return false;
                }
            }

            if (room.end_date !== null) {
                local = Time.localTime(room.end_date);
                if (local < now) {
                    return false;
                }
            }

            return true;
        },

        beforeChatRoomActive: function (room) {
            if (room.start_date === null) {
                return false;
            }
            return (new Date()) < Time.localTime(room.start_date);
        },

        afterChatRoomActive: function (room) {
            if (room.end_date === null) {
                return false;
            }
            return (new Date()) > Time.localTime(room.end_date);
        },

        initialize: function (init_chatroom_id) {
            chatroom_id = init_chatroom_id;

            chatCompileTemplates();
            chatAjaxRequestLoop();
            chatOnlinersAjaxRequestLoop();
        }
    };
    return that;
} ();

