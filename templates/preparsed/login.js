/*
 * login.js
 *
 *
 * make one call to initializeLogin() on document ready.
 *
 * ajaxRequest() will be called when someone logs in or out.
 *
 */

var template_login = (<r><![CDATA[{% include 'login_area.jst.html' %}]]></r>).toString();

var template_login_s = null;

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
    $("#login").html(Jst.evaluateCompiled(template_login_s, state_login));

    displayCorrectly($("#loginFormDiv"), loginFormDisplayed);
    displayCorrectly($("#loginFormError"), loginFormError);

    $("#signIn").click(function(){
        loginFormDisplayed = ! loginFormDisplayed;
        loginFormError = false;
        updateLogin();
        return false;
    });
    $("#signOut").click(function(){
        $.ajax({
            url: "/ajax/logout/",
            type: 'GET',
            success: function(){
                ajaxRequest();
                loginAjaxRequest();
            },
            error: function(){
                loginFormError = true;
                updateLogin();
                ajaxRequest();
                loginAjaxRequest();
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

function compileLoginTemplates() {
    template_login_s = Jst.compile(template_login);
}

function loginAjaxRequestLoop() {
    loginAjaxRequest();
    setTimeout(loginAjaxRequestLoop, 10000);
}

function loginInitialize() {
    compileLoginTemplates();
    loginAjaxRequestLoop();

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
                ajaxRequest();
                loginAjaxRequest();
            },
            error: function(){
                loginFormError = true;
                updateLogin();
                ajaxRequest();
                loginAjaxRequest();
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
}
