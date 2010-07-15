/*
 * chat.js - include this if you have a chat room on the page.
 *
 * Dependencies:
 *  jst-parser 0.4.0 - http://github.com/superjoe30/jst-parser
 *  Time - needs to already be initialized
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
    var template_chat = "{% filter escapejs %}{% include 'chat/box.jst.html' %}{% endfilter %}";
    var template_onliners = "{% filter escapejs %}{% include 'chat/onliners.jst.html' %}{% endfilter %}";
    var template_cannot_say = "{% filter escapejs %}{% include 'chat/cannot_say.jst.html' %}{% endfilter %}";
    var template_say = "{% filter escapejs %}{% include 'chat/say.jst.html' %}{% endfilter %}";
    
    // compiled templates
    var template_chat_s = null;
    var template_onliners_s = null;
    var template_cannot_say_s = null;
    var template_say_s = null;

    var state = {
        user: null,
        room: null,
        messages: [],
        urls: {
            say: "{% filter escapejs %}{% url chat.say %}{% endfilter %}",
            hear: "{% filter escapejs %}{% url chat.hear %}{% endfilter %}",
            onliners: "{% filter escapejs %}{% url chat.onliners %}{% endfilter %}",
            userpage: function (username) {
                return "{% filter escapejs %}{% url userpage '[~~~~]' %}{% endfilter %}".replace("[~~~~]", username);
            }
        },
        onliners: null
    };
    var chat_can_say = null;

    var last_message_id = null;
    var chat_temp_msg_count = 0;
    
    var chatroom_id;

    // private functions:
    function scrollToLastMessage() {
        $("#chatroom-outer-box").animate({ scrollTop: $("#chatroom-outer-box").attr('scrollHeight')}, 500);
    }

    // returns true if chat box is scrolled to the bottom
    function scrolledToBottom() {
        var container = $("#chatroom-outer-box");
        return (container.scrollTop() === container.attr('scrollHeight') - container.height());
    }

    function say(msg_to_post) {
        // add the message and clear the box
        var new_message = {
            'room': chatroom_id,
            'type': that.message_type.MESSAGE,
            'author': state.user,
            'message': msg_to_post,
            'timestamp': Time.serverTime(new Date())
        };
        var scroll = scrolledToBottom();

        new_message.author.username = state.user.username;
        state.messages.push(new_message);
        ++chat_temp_msg_count;
        updateChat();

        if (scroll) {
            scrollToLastMessage();
        }
    }

    function chatAddClicksToSay() {
        $("#chat-say-text").keydown(function(event){
            if (event.keyCode === 13) {
                // say something in chat
                var msg_to_post = $("#chat-say-text").attr('value');
                if (msg_to_post === '') {
                    return false;
                }
                $("#chat-say-text").attr('value','');
                $.ajax({
                    url: state.urls.say,
                    type: 'POST',
                    dataType: 'text',
                    data: {
                        'room': chatroom_id,
                        'message': msg_to_post
                    },
                    success: function(){
                    },
                    error: function(){
                        // TODO: show some kind of error message
                    }
                });
                say(msg_to_post);
                return false;
            }
        });
    }

    function updateChat() {
        var new_chat_can_say;
        var different;
        
        if (state.room === null || state.user === null) {
            return;
        }
        
        new_chat_can_say = that.chatRoomActive(state.room) &&
            state.user.is_authenticated &&
            state.user.permission_write;
        different = new_chat_can_say !== chat_can_say;
        chat_can_say = new_chat_can_say;
        if (different) {
            $("#chatroom-say").html(Jst.evaluate(template_say_s, state));
            chatAddClicksToSay();
            $("#chatroom-cannot-say").html(Jst.evaluate(template_cannot_say_s, state));
        }

        if (scrolledToBottom()) {
            $("#chatroom-outer-box").html(Jst.evaluate(template_chat_s, state));
        }

        if (chat_can_say) {
            $("#chatroom-cannot-say").hide();
            $("#chatroom-say").show();
        } else {
            $("#chatroom-cannot-say").show();
            $("#chatroom-say").hide();
        }

        // highlight messages that mention the user
        if (state.user !== null) {
            $("#chatroom .msg .imsg").each(function(index, item){
                if ($(item).html().toLowerCase().indexOf(
                    state.user.username.toLowerCase()) !== -1)
                {
                    $(item).parent().addClass('highlight');
                }
            });
        }
    }

    function updateChatOnliners() {
        $("#chatroom-outer-onliners").html(Jst.evaluate(template_onliners_s, state));
    }

    function chatOnlinersAjaxRequest() {
        $.getJSON(state.urls.onliners,
            {
                "room": chatroom_id
            },
            function(data){
                var onlinerCount = 0;

                if (data === null) {
                    return;
                }

                if (data.success === false) {
                    return;
                }

                if (data.data.length) {
                    onlinerCount = data.data.length;
                }
                
                if (onlinerCount > 0) {
                    data.data.sort(function(a,b){
                        var alc = a.username.toLowerCase();
                        var blc = b.username.toLowerCase();
                        if (alc > blc) {
                            return 1;
                        } else if (alc < blc) {
                            return -1;
                        } else {
                            return 0;
                        }
                    });
                }
                state.onliners = data.data;
                $("#chatroom .onliner-count").html(onlinerCount);
                
                updateChatOnliners();
            });
    }

    function onlinerAction(user_id, func) {
        var i;
        for (i=0; i<state.onliners.length; ++i) {
            if (state.onliners[i].id === user_id) {
                func(i);
            }
        }
    }

    function userJoin(user_id) {
    }

    function chatAjaxRequest() {
        $.getJSON(state.urls.hear,
            {
                "last_message": last_message_id,
                "room": chatroom_id
            },
            function(data){
                if (data === null) {
                    return;
                }

                // clear temporary messages
                while (chat_temp_msg_count > 0) {
                    state.messages.pop();
                    --chat_temp_msg_count;
                }

                // see if we're at the bottom of the div
                var scroll = scrolledToBottom();

                state.room = data.room;
                state.user = data.user;

                // sort incoming messages
                var messageCount = 0;
                if (data.messages.length) {
                    messageCount = data.messages.length;
                }
                if (messageCount > 0) {
                    data.messages.sort(function(a,b){
                        return a.id - b.id;
                    });
                }

                // return the index of where a new message should be inserted.
                // -1 if the message already exists
                function getMessageIndex(id) {
                    // loop backwards through the array until we find the
                    // slot for the message
                    var i;
                    for (i=state.messages.length-1; i>=0; --i) {
                        if (state.messages[i].id < id) {
                            return i+1;
                        } else if (state.messages[i].id === id) {
                            return -1;
                        }
                    }
                    // there are no messages
                    return 0;
                }

                // insert the new messages into the sorted list
                // if the id is already in the array, discard it.
                var insertIndex;
                var prevId;
                var i;
                function removeOnliner(index) {
                    state.onliners.splice(index, 1);
                }
                for (i=0; i<messageCount; ++i) {
                    // if it's a join or part, affect state.onliners
                    if (last_message_id && state.onliners) {
                        if (data.messages[i].type === that.message_type.JOIN) {
                            onlinerAction(data.messages[i].author.id, removeOnliner);
                        } else if (data.messages[i].type === that.message_type.LEAVE) {
                            state.onliners.push(data.messages[i].author);
                        }
                    }
                    insertIndex = getMessageIndex(data.messages[i].id);
                    if (insertIndex !== -1) {
                        state.messages.splice(insertIndex, 0, data.messages[i]);

                        // if this message is on a different day than previous,
                        // insert a heading
                        if (insertIndex > 0) {
                            lastMessageDate = state.messages[insertIndex-1].timestamp;
                            prevId = state.messages[insertIndex-1].id;
                        } else {
                            // arbitrary early date ;)
                            lastMessageDate = new Date("November 5, 1988 23:30:04");
                            prevId = -1;
                        }
                        if (Time.isDifferentDay(data.messages[i].timestamp,
                            lastMessageDate))
                        {
                            
                            state.messages.splice(insertIndex, 0, {
                                id: (data.messages[i].id + prevId) / 2,
                                type: that.message_type.HEADER,
                                timestamp: data.messages[i].timestamp
                            });
                        }
                    }
                }
                if (messageCount > 0) {
                    last_message_id = data.messages[messageCount-1].id;
                }

                if (that.beforeChatRoomActive(state.room)) {
                    last_message_id = null;
                }

                updateChat();
                if (state.onliners !== null) {
                    updateChatOnliners();
                }

                if (scroll) {
                    scrollToLastMessage();
                }
            });
    }

    function chatAjaxRequestLoop() {
        chatAjaxRequest();
        setTimeout(chatAjaxRequestLoop, messageRequestTimeout);
    }

    function chatOnlinersAjaxRequestLoop() {
        chatOnlinersAjaxRequest();
        setTimeout(chatOnlinersAjaxRequestLoop, onlinersRequestTimeout);
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
            NOTICE: 5,

            HEADER: 99
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

        beforeChatRoomActive: function () {
            if (state.room.start_date === null) {
                return false;
            }
            return (new Date()) < Time.localTime(state.room.start_date);
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

