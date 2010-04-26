var template_login = (<r><![CDATA[{% include 'arena/login.jst.html' %}]]></r>).toString();
var template_available = (<r><![CDATA[{% include 'arena/available.jst.html' %}]]></r>).toString();
var template_owned = (<r><![CDATA[{% include 'arena/owned.jst.html' %}]]></r>).toString();

// true if we display the input text boxes
var loginFormDisplayed = false;
var loginFormError = false;
var state_login;
var state_available;
var state_owned;

// convert ISO date to JS date
Date.prototype.setISO8601 = function(dString){
    var regexp = /(\d\d\d\d)(-)?(\d\d)(-)?(\d\d)(T)?(\d\d)(:)?(\d\d)(:)?(\d\d)(\.\d+)?(Z|([+-])(\d\d)(:)?(\d\d))/;
     
    if (dString.toString().match(new RegExp(regexp))) {
        var d = dString.match(new RegExp(regexp));
        var offset = 0;
         
        this.setUTCDate(1);
        this.setUTCFullYear(parseInt(d[1],10));
        this.setUTCMonth(parseInt(d[3],10) - 1);
        this.setUTCDate(parseInt(d[5],10));
        this.setUTCHours(parseInt(d[7],10));
        this.setUTCMinutes(parseInt(d[9],10));
        this.setUTCSeconds(parseInt(d[11],10));
        if (d[12])
            this.setUTCMilliseconds(parseFloat(d[12]) * 1000);
        else
            this.setUTCMilliseconds(0);
        if (d[13] != 'Z') {
            offset = (d[15] * 60) + parseInt(d[17],10);
            offset *= ((d[14] == '-') ? -1 : 1);
            this.setTime(this.getTime() - offset * 60 * 1000);
        }
    } else {
        this.setTime(Date.parse(dString));
    }
    return this;
};

// pads an integer with a zero if necessary and returns a string
function pad(num) {
    return ((num < 10) ? "0" : "") + num;
}

// takes milliseconds and returns a nice display like 0:00
function timeDisplay(ms) {
    var sec = ms / 1000;
    var min = sec / 60;
    var hr = min / 60;

    if (hr >= 1) {
        hr = Math.floor(hr);
        min = Math.floor(min - hr * 60);
        sec = Math.floor(sec - (hr * 60 + min) * 60);
        return hr + ":" + pad(min) + ":" + pad(sec);
    } else {
        min = Math.floor(min);
        sec = Math.floor(sec - min * 60);
        return min + ":" + pad(sec);
    }
}

// return how many minutes until a server time in a nice display format
function timeDisplayUntil(serverTime) {
    var local = localTime(serverTime);
    var now = new Date();
    return timeDisplay(local - now);
}

// return how many minutes since a server time in a nice display format
function timeDisplaySince(serverTime) {
    var local = localTime(serverTime);
    var now = new Date();
    return timeDisplay(now - local);
}

// make sure parameter is converted to a date
function coerceDate(date_or_string) {
    if (date_or_string instanceof String) {
        out = new Date();
        out.setISO8601(date_or_string);
        return out;
    } else if (date_or_string instanceof Date) {
        return date_or_string;
    } else {
        throw("Error (coerceDate): " + date_or_string + " is not a date or string.");
    }
}

// convert a sever time to a local time
function localTime(serverTime) {
    serverTime = coerceDate(serverTime);

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

function updateAvailable() {
    $("#available").html(Jst.evaluate(template_available, state_available));
}

function updateOwned() {
    $("#owned").html(Jst.evaluate(template_owned, state_owned));
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
        $.ajax({
            url: "/ajax/login/",
            type: 'POST',
            dataType: 'text',
            data: {
                'username': $("#loginName").attr('value'),
                'password': $("#loginPassword").attr('value'),
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
        loginFormDisplayed = false;
        updateLogin();
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
            if (data == null)
                return;

            state_available = data;
            updateAvailable();
        });

    $.getJSON("/arena/ajax/owned/",
        function(data){
            if (data == null)
                return

            state_owned = data;
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

