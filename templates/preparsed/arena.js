var template_login = (<r><![CDATA[{% include 'login_area.jst.html' %}]]></r>).toString();
var template_available = (<r><![CDATA[{% include 'arena/available.jst.html' %}]]></r>).toString();
var template_owned = (<r><![CDATA[{% include 'arena/owned.jst.html' %}]]></r>).toString();

// true if we display the input text boxes
var loginFormDisplayed = false;
var loginFormError = false;
var state_login = null;
var state_available = null;
var state_owned = null;

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
    if (date_or_string instanceof Date)
        return date_or_string;
    else
        return new Date(date_or_string);
}

// pretty print a datetime
function formatDate(datetime) {
    return datetime.toString();
}

// convert a sever time to a local time
function localTime(serverTime) {
    serverTime = coerceDate(serverTime);

    // find the difference between the local and the server time
    var diff = server_time - local_time;
    // apply the differece to the input serverTime
    return new Date(serverTime - diff);
}

// return in a nice printable string how much time until then
function printableTimeUntil(serverTime) {
    return printableTimeDiff(secondsUntil(serverTime));
}

function printableTimeSince(serverTime) {
    return printableTimeDiff(secondsSince(serverTime));
}

function printableTimeDiff(seconds) {
    var minutes = seconds / 60;
    var hours = minutes / 60;
    var days = hours / 24;
    var weeks = days / 7;
    var months = days / 30;
    var years = days / 365;

    if (years >= 1)
        return plural(Math.floor(years), "year", "years");

    if (months >= 1)
        return plural(Math.floor(months), "month", "months");

    if (weeks >= 1)
        return plural(Math.floor(weeks), "week", "weeks");

    if (days >= 1)
        return plural(Math.floor(days), "day", "days");

    if (hours >= 1)
        return plural(Math.floor(hours), "hour", "hours");

    if (minutes >= 1)
        return plural(Math.floor(minutes), "minute", "minutes");

    return plural(Math.floor(seconds), "second", "seconds");
}

function plural(n, singular, plural) {
    return n + " " + ((n == 1) ? singular : plural);
}

function secondsUntil(serverTime) {
    // convert to local time
    var local = localTime(serverTime);
    // get current time
    var current = new Date();
    // return the difference
    return (local - current)/1000;
}

function secondsSince(serverTime) {
    // convert to local time
    var local = localTime(serverTime);
    // get current time
    var current = new Date();
    // return the difference
    return (current - local)/1000;
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

function addClicksToCompo(compo) {
    $("#compo-" + compo.id + "-remove").click(function(){
        $.ajax({
            url: "/arena/ajax/remove/" + compo.id + "/",
            type: 'GET',
            success: function(){
                ajaxRequest()
            },
            error: function(){
                ajaxRequest()
            }
        });
        return false;
    });
    $("#compo-" + compo.id + "-bookmark").click(function(){
        $.ajax({
            url: "/arena/ajax/bookmark/" + compo.id + "/",
            type: 'GET',
            success: function(){
                ajaxRequest()
            },
            error: function(){
                ajaxRequest()
            }
        });
        return false;
    });
}

function setBookmarkedProperty(data, value) {
    for(var i=0; i<data.ongoing.length; ++i)
        data.ongoing[i].bookmarked = value;

    for(var i=0; i<data.closed.length; ++i)
        data.closed[i].bookmarked = value;

    for(var i=0; i<data.upcoming.length; ++i)
        data.upcoming[i].bookmarked = value;
}

function addClicksToSection(data) {
    for(var i=0; i<data.ongoing.length; ++i)
        addClicksToCompo(data.ongoing[i]);

    for(var i=0; i<data.closed.length; ++i)
        addClicksToCompo(data.closed[i]);

    for(var i=0; i<data.upcoming.length; ++i)
        addClicksToCompo(data.upcoming[i]);
}

function updateAvailable() {
    if (state_available == null)
        return;

    $("#available").html(Jst.evaluate(template_available, state_available));

    addClicksToSection(state_available);
}

function updateOwned() {
    if (state_owned == null)
        return;

    $("#owned").html(Jst.evaluate(template_owned, state_owned));

    addClicksToSection(state_owned);
}

function updateLogin() {
    if (state_login == null)
        return;

    // populate div with template parsed with json object
    $("#login").html(Jst.evaluate(template_login, state_login));

    displayCorrectly($("#loginFormDiv"), loginFormDisplayed);
    displayCorrectly($("#loginFormError"), loginFormError);

    $("#signIn").click(function(){
        loginFormDisplayed = ! loginFormDisplayed;
        loginFormError = false;
        updateLogin();
        return false;
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
        return false;
    });
    $("#cancelLoginButton").click(function(){
        loginFormDisplayed = false;
        updateLogin();
        return false;
    });
    $("#signOut").click(function(){
        $.ajax({
            url: "/ajax/logout/",
            type: 'GET',
            success: function(){
                ajaxRequest()
            },
            error: function(){
                loginFormError = true;
                updateLogin();
                ajaxRequest()
            }
        });
        return false;
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

            setBookmarkedProperty(state_available, false);
            updateAvailable();
        });

    $.getJSON("/arena/ajax/owned/",
        function(data){
            if (data == null)
                return

            state_owned = data;
            setBookmarkedProperty(state_owned, true);
            updateOwned();
        });
}

function ajaxRequestLoop() {
    ajaxRequest();
    setTimeout(ajaxRequestLoop, 10000);
}

function updateCompetitionsLoop() {
    updateAvailable();
    updateOwned();
    setTimeout(updateCompetitionsLoop, 1000);
}

$(document).ready(function(){
    ajaxRequestLoop();
    updateCompetitionsLoop();
});

