var template_login = (<r><![CDATA[{% include 'arena/login.jst.html' %}]]></r>).toString();
var template_available = (<r><![CDATA[{% include 'arena/available.jst.html' %}]]></r>).toString();
var template_owned = (<r><![CDATA[{% include 'arena/owned.jst.html' %}]]></r>).toString();

function refreshDisplay() {
    $.getJSON("/ajax/login_state/",
        function(data){
            $("#login").html(Jst.evaluate(template_login, data));
        });

    setTimeout(refreshDisplay, 10000);
}

$(document).ready(function(){
    refreshDisplay();
});

