var template_login = (<r><![CDATA[{% include 'arena/login.jst.html' %}]]></r>).toString();
var template_available = (<r><![CDATA[{% include 'arena/available.jst.html' %}]]></r>).toString();
var template_owned = (<r><![CDATA[{% include 'arena/owned.jst.html' %}]]></r>).toString();

// true if we display the input text boxes
var loginFormDisplayed = false;
var loginFormError = false;
var state_login;
var state_available;
var state_owned;

// convert a sever time to a local time
function localTime(serverTime) {
    // find the difference between the local and the server time
    var diff = server_time - local_time;
    // apply the differece to the input serverTime
    return new Date(serverTime - diff);
}

function secondsUntil(serverTime) {
    // convert to local time
    var local = localTime(serverTime);
    // get current time
    var current = new Date();
    // return the difference
    return (local - current)/1000;
}

// return whether an element is visible or not
function isVisible(div) {
    return ! (div.css("visibility") == "hidden" || 
                div.css("display") == "none");
}

// show an element if it should be shown, hide if it should be hidden
function displayCorrectly(div, visible) {
    var actuallyVisible = isVisible(div);
    if (visible && ! actuallyVisible)
        div.show('fast');
    else if(! visible && actuallyVisible)
        div.hide('fast');
}

function updateLogin() {
    // populate div with template parsed with json object
    $("#login").html(Jst.evaluate(template_login, state_login));

    displayCorrectly($("#loginFormDiv"), loginFormDisplayed);
    displayCorrectly($("#loginFormError"), loginFormError);

    // replace links with ajax
    $("#signIn").click(function(){
        loginFormDisplayed = ! loginFormDisplayed;
        loginFormError = false;
        updateLogin();
    });
    $("#loginButton").click(function(){
        loginFormDisplayed = false;
        updateLogin();
        $.ajax({
            url: "/ajax/login/",
            type: 'POST',
            dataType: 'text',
            data: {
                'user': $("#loginName").attr('value'),
                'pass': $("#loginPassword").attr('value'),
            },
            success: function(){
                ajaxRequest()
            },
            error: function(){
                loginFormError = true;
                updateLogin();
                ajaxRequest()
            }
        });
    });
    $("#cancelLoginButton").click(function(){
        loginFormDisplayed = false;
        updateLogin();
    });
}

function ajaxRequest() {
    $.getJSON("/ajax/login_state/",
        function(data){
            if (data == null)
                return;

            state_login = data;
            updateLogin();
        });

    $.getJSON("/arena/ajax/available/",
        function(data){
            if (data != null)
                $("#available").html(Jst.evaluate(template_available, data));
        });

    $.getJSON("/arena/ajax/owned/",
        function(data){
            if (data != null)
                $("#owned").html(Jst.evaluate(template_owned, data));
        });
}

function ajaxRequestLoop() {
    ajaxRequest();
    setTimeout(ajaxRequestLoop, 10000);
}

$(document).ready(function(){
    ajaxRequestLoop();
});

