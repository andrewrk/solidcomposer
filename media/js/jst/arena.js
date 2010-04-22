var template_login = (<r><![CDATA[<% if (user.is_authenticated) { %>
    
    <a href="/user/<%=user.username%>"><%=user.username%></a>
<a href="/user//"> <span class="points">()</span></a>

    
    <a href="/account/">settings</a>
    <a href="/logout/">sign out</a>
<% } else { %>
    Not logged in.
    <a href="/login/?next=<%= window.location %>">sign in</a>
    <a href="/register/?next=<%= window.location %>">register</a>
<% } %>
]]></r>).toString();
var template_available = (<r><![CDATA[]]></r>).toString();
var template_owned = (<r><![CDATA[]]></r>).toString();

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

