var SCWorkbench = function () {
    // private variables
    var that;

    // configurable stuff
    var stateRequestTimeout = 10000;

    var template_home = "{% filter escapejs %}{% include 'workbench/home.jst.html' %}{% endfilter %}";

    var template_home_s = null;

    var state = {
        urls: {
            ajax_home: "{% filter escapejs %}{% url workbench.ajax_home %}{% endfilter %}",
            band: function(id) {
                return "{% filter escapejs %}{% url workbench.band 0 %}{% endfilter %}".replace(0, id);
            },
            bandFanPage: function(id) {
                return "{% filter escapejs %}{% url music.band 0 %}{% endfilter %}".replace(0, id);
            },
            acceptInvite: "{% filter escapejs %}{% url workbench.ajax_accept_invite %}{% endfilter %}",
            ignoreInvite: "{% filter escapejs %}{% url workbench.ajax_ignore_invite %}{% endfilter %}"
        },
        json: null,
        roleNames: [
            "Manager",
            "Band member",
            "Critic",
            "Fan",
            "Banned"
        ]
    }
    
    // private functions
    function updateHome() {
        if (state.json === null) {
            return;
        }

        $("#workbench").html(Jst.evaluate(template_home_s, state));

        $("#workbenchSignIn").click(Login.showSignIn);

        // accept/ignore invitation buttons
        var inviteAction = function() {
            var index = $(this).attr('index');
            var accept = $(this).attr('class') === "accept"; 
            var url;
            var err_msg;
            if (accept) {
                url = state.urls.ajax_accept_invite;
                err_msg = "Error accepting invite: ";
            } else {
                url = state.urls.ajax_ignore_invite;
                err_msg = "Error ignoring invite: ";
            }
            $.getJSON(url,
                {
                    invitation: state.json.invites[index].id
                },
                function(data) {
                    if (data === null) {
                        return;
                    }
                    if (data.success) {
                        state.json.invites.splice(index, 1);
                        updateHome();
                    } else {
                        alert(err_msg + data.reason);
                    }
                }
            );
        };
        $(".action a.accept").click(inviteAction);
        $(".action a.ignore").click(inviteAction);
    }

    function ajaxRequestLoop() {
        that.ajaxRequest();
        setTimeout(ajaxRequestLoop, stateRequestTimeout);
    }

    function compileTemplates() {
        template_home_s = Jst.compile(template_home);
    }

    function ajaxRequestHome() {
        $.getJSON(
            state.urls.ajax_home,
            {
                // no data to send
            },
            function(data){
                if (data === null) {
                    return;
                }

                state.json = data;
                updateHome();
            }
        );
    }

    that = {
        // public variables
        
        // public functions
        initialize: function () {
            compileTemplates();
            ajaxRequestLoop();
        },
        
        ajaxRequest: function () {
            ajaxRequestHome();
        }
    };
    return that;
} ();

$(document).ready(function(){
    Time.initialize(server_time, local_time);

    Login.initialize();
    Login.addStateChangeCallback(SCWorkbench.ajaxRequest);

    SCWorkbench.initialize();
});


