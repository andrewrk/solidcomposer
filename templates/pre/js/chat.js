/*
 * chat.js - include this if you have a chat room on the page.
 *
 * Dependencies:
 *  jst-parser 0.4.0 - http://github.com/andrewrk/jst-parser
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
    var template_message_row = "{% filter escapejs %}{% include 'chat/message_row.jst.html' %}{% endfilter %}";
    
    // compiled templates
    var template_chat_s = null;
    var template_onliners_s = null;
    var template_cannot_say_s = null;
    var template_say_s = null;
    var template_message_row_s = null;

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

    var pageScrollDelta = 200;
    
    // private functions:
    function scrollToLastMessage() {
        var container = $("#chatroom-outer-box");
        container.animate({ scrollTop: container.attr('scrollHeight') - container.height()}, 200);
    }

    // returns true if chat box is scrolled to the bottom
    function scrolledToBottom() {
        var container = $("#chatroom-outer-box");
        return (container.scrollTop() >= container.attr('scrollHeight') - container.height());
    }

    function say(msg_to_post) {
        var type = that.message_type.MESSAGE;
        var words;
        var command;
        if (msg_to_post.length >= 2) {
            if (msg_to_post[0] === '/' && msg_to_post[1] !== '/') {
                // command
                words = msg_to_post.split(/\s+/);
                command = words[0].substring(1, words[0].length).toLowerCase();
                if (command === 'me') {
                    type = that.message_type.ACTION;
                    msg_to_post = msg_to_post.substring(words[0].length+1, msg_to_post.length)
                }
            }
        }

        $.ajax({
            url: state.urls.say,
            type: 'POST',
            dataType: 'text',
            data: {
                'room': chatroom_id,
                'message': msg_to_post,
                'type': type
            },
            success: function(){
            },
            error: function(){
                // TODO: show some kind of error message
            }
        });

        // add the message and clear the box
        var new_message = {
            'room': chatroom_id,
            'type': type,
            'author': state.user,
            'message': msg_to_post,
            'timestamp': Time.serverTime(new Date())
        };
        var scroll = scrolledToBottom();

        new_message.author.username = state.user.username;
        state.messages.push(new_message);
        ++chat_temp_msg_count;

        // instead of updating everything, which could be slow if there are a lot of messages,
        // we simply add the row.
        var content = Jst.evaluate(template_message_row_s, {msg: new_message});
        $(".lastmsg").before(content);
        processMessageStyle($(".lastmsg").prev().find('.imsg'));

        if (scroll) {
            scrollToLastMessage();
        }
    }

    function getCursorPos(textbox) {
        if (textbox.selectionStart) {
            return textbox.selectionStart;
        } else if (document.selection) {
            // wtf kind of API is this
            var sel;
            if (document.selection) {
                textbox.focus();
                sel = document.selection.createRange();
                sel.moveStart('character', -textbox.value.length);
                return sel.text.length;
            }
        }
    }

    function setCursorPos(textbox, pos) {
        textbox.focus();
        if (textbox.selectionStart) {
            textbox.setSelectionRange(pos, pos);
        } else if (textbox.createTextRange) {
            var range = textbox.createTextRange();
            range.move('character', pos);
            range.select();
        }
    }

    // returns {match: the longest common beginning to all the strings, unique: true if it was unique}
    function sameBeginning(stringList) {
        var match = "";
        var proposedChar;
        var i;
        var charIndex = 0;
        var endFlag = false;
        var str;
        do {
            endFlag = charIndex >= stringList[0].length - 1;
            proposedChar = stringList[0].substring(charIndex, charIndex+1);
            for (i=1; i<stringList.length; ++i) {
                str = stringList[i];

                if (str.substring(charIndex, charIndex+1) !== proposedChar) {
                    return {match: match, unique: false};
                }
                
                if (charIndex < str.length - 1) {
                    endFlag = false;
                }
            }

            match += proposedChar;
            ++charIndex;
        } while (! endFlag);

        return {match: match, unique: true};
    }

    function chatAddClicksToSay() {
        $("#chat-say-text").keydown(function(event){
            if (event.keyCode === 13) {
                // enter key
                event.preventDefault();
                // say something in chat
                var msg_to_post = $(this).val();
                if (msg_to_post === '') {
                    return false;
                }
                $(this).val('');
                say(msg_to_post);
                return false;
            } else if (event.keyCode === 9) {
                // tab key
                event.preventDefault();
                if (state.onliners !== null) {
                    // try to finish the current word as a username
                    var currentText = $(this).val();
                    var cursorPos = getCursorPos(this);
                    var atEnd = cursorPos === currentText.length;
                    var prevText = currentText.substring(0, cursorPos);
                    if (prevText === '') {
                        return false;
                    }
                    var words = prevText.split(/\s+/);
                    var beginningMatch;
                    if (words.length > 0) {
                        beginningMatch = words[words.length-1];
                    } else {
                        beginningMatch = "";
                    }
                    // if beginningMatch matches any of the online people, tab complete.
                    var i;
                    var matches = [];
                    for (i=0; i<state.onliners.length; ++i) {
                        var onlinerName = state.onliners[i].username;
                        if (onlinerName.substring(0, beginningMatch.length).toLowerCase() === beginningMatch.toLowerCase()) {
                            matches.push(onlinerName);
                        }
                    }
                    var newText;
                    var result;
                    var space;
                    if (matches.length > 0) {
                        result = sameBeginning(matches);
                        space = result.unique ? " " : "";
                        newText = currentText.substring(0, cursorPos - beginningMatch.length)
                            + result.match + space + currentText.substring(cursorPos, currentText.length);
                        $(this).val(newText);
                        setCursorPos(this, cursorPos + result.match.length - beginningMatch.length + space.length);
                    }
                }
                
                
                return false;
            } else if (event.keyCode === 33) {
                // page up
                event.preventDefault();
                var box = $("#chatroom-outer-box");
                box.scrollTop(box.scrollTop() - pageScrollDelta);
                return false;
            } else if (event.keyCode === 34) {
                // page down
                event.preventDefault();
                var box = $("#chatroom-outer-box");
                box.scrollTop(box.scrollTop() + pageScrollDelta);
                return false;
            }
        });
    }

    function processMessageStyle(item) {
        if ($(item).html().toLowerCase().indexOf(
            state.user.username.toLowerCase()) !== -1)
        {
            $(item).parent().addClass('highlight');
        }
    }

    function updateChatPeripherals() {
        if (state.room === null || state.user === null) {
            return;
        }
        
        var new_chat_can_say = that.chatRoomActive(state.room) &&
            state.user.is_authenticated &&
            state.user.permission_write;
        var different = new_chat_can_say !== chat_can_say;
        chat_can_say = new_chat_can_say;
        if (different) {
            $("#chatroom-say").html(Jst.evaluate(template_say_s, state));
            chatAddClicksToSay();
            $("#chatroom-cannot-say").html(Jst.evaluate(template_cannot_say_s, state));
        }

        if (chat_can_say) {
            $("#chatroom-cannot-say").hide();
            $("#chatroom-say").show();
        } else {
            $("#chatroom-cannot-say").show();
            $("#chatroom-say").hide();
        }

    }

    function updateChat() {
        if (state.room === null || state.user === null) {
            return;
        }

        if (scrolledToBottom()) {
            $("#chatroom-outer-box").html(Jst.evaluate(template_chat_s, state));
            scrollToLastMessage();
        }

        // highlight messages that mention the user
        if (state.user !== null && state.user.is_authenticated) {
            $("#chatroom .msg .imsg").each(function(index, item) { processMessageStyle(item); });
        }

        updateChatPeripherals()
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
                            state.onliners.push(data.messages[i].author);
                        } else if (data.messages[i].type === that.message_type.LEAVE) {
                            onlinerAction(data.messages[i].author.id, removeOnliner);
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
                        if (Time.isDifferentDay(
                                Time.localTime(data.messages[i].timestamp),
                                Time.localTime(lastMessageDate)))
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
        template_message_row_s = Jst.compile(template_message_row);
    }

    function escapeHtml(text) {
        return text
            .toString()
            .replaceAll('&', '&amp;') // must be first
            .replaceAll('"', '&quot;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;');
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
            if (room === null) {
                return false;
            }
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
        },

        // parses a message and turns http:// into links and stuff.
        // note that the input is raw user message and the output has html in it.
        // so this function escapes html and stuff.
        formatMessage: function (message) {
            var safeMessage = escapeHtml(message);
            return safeMessage.replace(/(http:\/\/\S+)/g, "<a href=\"$1\" target=\"_BLANK\">$1</a>");
        }
    };
    return that;
} ();

