var template_status = (<r><![CDATA[{% include 'login_area.jst.html' %}]]></r>).toString();
var template_vote_status = (<r><![CDATA[{% include 'login_area.jst.html' %}]]></r>).toString();
var template_entries = (<r><![CDATA[{% include 'login_area.jst.html' %}]]></r>).toString();
var template_chat = (<r><![CDATA[{% include 'login_area.jst.html' %}]]></r>).toString();
var template_onliners = (<r><![CDATA[{% include 'login_area.jst.html' %}]]></r>).toString();

var state_compo = null;
var state_chat = null;

var chat_last_update = null;

function updateEverything() {
    //{'compo': state_compo, 'chat': state_chat}
}

function ajaxRequest() {
    loginAjaxRequest();
    
    $.getJSON("/arena/ajax/compo/" + competition_id + "/", function(data){
        if (data == null)
            return;

        state_compo = data;

        updateEverything();
    });

    $.getJSON("/ajax/chat/",
        {
            "latest_check": chat_last_update,
        },
        function(data){
            if (data == null)
                return;

            state_owned = data;
            if (data.user.is_authenticated)
                setBookmarkedProperty(state_owned, true);

            updateOwned();
        });
}

function ajaxRequestLoop() {
    ajaxRequest();
    setTimeout(ajaxRequestLoop, 10000);
}

$(document).ready(function(){
    ajaxRequestLoop();
});

