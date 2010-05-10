/*
 * login.js
 *
 * Make one call to initialize() on document ready.
 *
 * If you want a callback when someone logs in or out, use
 *
 * Login.addStateChangeCallback(function);
 *
 */

var Login = function () {
    // private variables:
    var that;

    // configurable stuff
    var stateRequestTimeout = 10000;

    var template_login = "{% filter escapejs %}{% include 'login_area.jst.html' %}{% endfilter %}";

    var template_login_s = null;

    // true if we display the input text boxes
    var loginFormDisplayed = false;

    var loginFormError = false;
    var state_login = null;
    
    var callbacks = [];

    // private functions
    function signalStateChanged() {
        var i;
        
        for (i=0; i<callbacks.length; ++i) {
            callbacks[i]();
        }
    }
    
    // return whether an element is visible or not
    function isVisible(div) {
        return ! (div.css("visibility") == "hidden" || 
                    div.css("display") == "none");
    }

    // show an element if it should be shown, hide if it should be hidden
    function displayCorrectly(div, visible) {
        var actuallyVisible = isVisible(div);
        if (visible && ! actuallyVisible) {
            div.show('fast');
        } else if(! visible && actuallyVisible) {
            div.hide('fast');
        }
    }

    function updateLogin() {
        if (state_login === null) {
            return;
        }

        // populate div with template parsed with json object
        $("#login").html(Jst.evaluate(template_login_s, state_login));

        displayCorrectly($("#loginFormDiv"), loginFormDisplayed);
        displayCorrectly($("#loginFormError"), loginFormError);

        $("#signIn").click(function(){
            loginFormDisplayed = ! loginFormDisplayed;
            loginFormError = false;
            updateLogin();
            if (loginFormDisplayed) {
                $("#loginName").focus();
            }
            return false;
        });
        $("#signOut").click(function(){
            $.ajax({
                url: "/ajax/logout/",
                type: 'GET',
                success: function(){
                    signalStateChanged();
                    loginAjaxRequest();
                },
                error: function(){
                    loginFormError = true;
                    updateLogin();
                    signalStateChanged();
                    loginAjaxRequest();
                }
            });
            return false;
        });
    }

    function loginAjaxRequest() {
        $.getJSON("/ajax/login_state/", function(data){
            if (data === null) {
                return;
            }

            state_login = data;
            updateLogin();
        });
    }

    function compileLoginTemplates() {
        template_login_s = Jst.compile(template_login);
    }

    function loginAjaxRequestLoop() {
        loginAjaxRequest();
        setTimeout(loginAjaxRequestLoop, stateRequestTimeout);
    }

    function sendLoginRequest() {
        $.ajax({
            url: "/ajax/login/",
            type: 'POST',
            dataType: 'json',
            data: {
                'username': $("#loginName").attr('value'),
                'password': $("#loginPassword").attr('value')
            },
            success: function(data){
                if (data.success) {
                    $("#loginName").attr('value','');
                    $("#loginPassword").attr('value','');
                    signalStateChanged();
                    loginAjaxRequest();
                } else {
                    alert("Unable to log in:\n" + data.err_msg);
                }
            },
            error: function(){
                alert("Error logging in.");
                loginFormError = true;
                updateLogin();
                signalStateChanged();
                loginAjaxRequest();
            }
        });
        loginFormDisplayed = false;
        updateLogin();
        return false;
    }


    that = {
        // public variables

        // public methods
        initialize: function () {
            compileLoginTemplates();
            loginAjaxRequestLoop();

            $("#loginButton").click(sendLoginRequest);
            $("#loginName").keydown(function(event){
                if (event.keyCode == 13) {
                    sendLoginRequest();
                    return false;
                }
                if (event.keyCode == 27) {
                    loginFormDisplayed = false;
                    updateLogin();
                    return false;
                }
            });
            $("#loginPassword").keydown(function(event){
                if (event.keyCode == 13) {
                    sendLoginRequest();
                    return false;
                }
                if (event.keyCode == 27) {
                    loginFormDisplayed = false;
                    updateLogin();
                    return false;
                }
            });

            $("#cancelLoginButton").click(function(){
                loginFormDisplayed = false;
                updateLogin();
                return false;
            });
        },
        
        addStateChangeCallback: function(func) {
            callbacks.push(func);
        }
    };
    return that;
} ();

