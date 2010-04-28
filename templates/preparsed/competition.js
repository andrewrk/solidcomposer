var template_status = (<r><![CDATA[{% include 'arena/compo_status.jst.html' %}]]></r>).toString();
var template_info = (<r><![CDATA[{% include 'arena/compo_info.jst.html' %}]]></r>).toString();
var template_vote_status = (<r><![CDATA[{% include 'arena/vote_status.jst.html' %}]]></r>).toString();
var template_entries = (<r><![CDATA[{% include 'login_area.jst.html' %}]]></r>).toString();
var template_chat = (<r><![CDATA[{% include 'login_area.jst.html' %}]]></r>).toString();
var template_onliners = (<r><![CDATA[{% include 'login_area.jst.html' %}]]></r>).toString();

var state_compo = null;
var state_chat = null;

var chat_last_update = null;

function updateChat() {
    // TODO
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

