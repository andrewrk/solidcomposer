var template_login = (<r><![CDATA[{% include 'login_area.jst.html' %}]]></r>).toString();

// true if we display the input text boxes
var loginFormDisplayed = false;

var loginFormError = false;
var state_login = null;

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

function loginAjaxRequest() {
    $.getJSON("/ajax/login_state/", function(data){
        if (data == null)
            return;

        state_login = data;
        updateLogin();
    });
}
