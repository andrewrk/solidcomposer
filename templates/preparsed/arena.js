var template_login = (<r><![CDATA[{% include 'arena/login.jst.html' %}]]></r>).toString();
var template_available = (<r><![CDATA[{% include 'arena/available.jst.html' %}]]></r>).toString();
var template_owned = (<r><![CDATA[{% include 'arena/owned.jst.html' %}]]></r>).toString();

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

function refreshDisplay() {
    $.getJSON("/ajax/login_state/",
        function(data){
            if (data != null)
                $("#login").html(Jst.evaluate(template_login, data));
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

    setTimeout(refreshDisplay, 10000);
}

$(document).ready(function(){
    refreshDisplay();
});

