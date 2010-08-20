var SCWorkbench = function () {
    // private variables
    var that;

    // configurable stuff
    var stateRequestTimeout = 10000;

    // templates
    var templateHome = "{% filter escapejs %}{% include 'workbench/home.jst.html' %}{% endfilter %}";
    var templateHomeCompiled = null;

    // the id of the last LogEntry we got from the server.
    var lastActivityId = null;

    // the context we pass to the templates
    var state = {
        urls: {
            ajax_home: "{% filter escapejs %}{% url workbench.ajax_home %}{% endfilter %}",
            band: function(id) {
                return "{% filter escapejs %}{% url workbench.band 0 %}{% endfilter %}".replace(0, id);
            },
            acceptInvite: "{% filter escapejs %}{% url workbench.ajax_accept_invite %}{% endfilter %}",
            ignoreInvite: "{% filter escapejs %}{% url workbench.ajax_ignore_invite %}{% endfilter %}",
            userpage: function (username) {
                return "{% filter escapejs %}{% url userpage '[~~~~]' %}{% endfilter %}".replace("[~~~~]", username);
            },
            project: function(id, band_id) {
                return "{% filter escapejs %}{% url workbench.project 0 1 %}{% endfilter %}".replace("0",
                    "[~~band_id~~]").replace("1", id).replace("[~~band_id~~]", band_id);
            },
            project_version: function(project_id, band_id, version_number) {
                return this.project(project_id, band_id) + "#version" + version_number;
            }
        },
        json: null,
        logEntries: [],
        roleNames: [
            "Manager",
            "Band member",
            "Critic",
            "Fan",
            "Banned"
        ],
        entryTypeEnum:{% include 'workbench/entryTypeEnum.jst.html' %} 
    };
    
    // private functions
    function updateHome() {
        if (state.json === null) {
            return;
        }

        $("#workbench").html(Jst.evaluate(templateHomeCompiled, state));
        SCTips.addUi("#workbench");

        $("#workbenchSignIn").click(Login.showSignIn);

        // accept/ignore invitation buttons
        var inviteAction = function() {
            var index = $(this).attr('data-index');
            var accept = $(this).attr('class') === "accept"; 
            var url;
            var err_msg;
            if (accept) {
                url = state.urls.acceptInvite;
                err_msg = "Error accepting invite: ";
            } else {
                url = state.urls.ignoreInvite;
                err_msg = "Error ignoring invite: ";
            }
            $.post(url,
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
                }, 'json'
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
        templateHomeCompiled = Jst.compile(templateHome);
    }

    function ajaxRequestHome() {
        $.getJSON(
            state.urls.ajax_home,
            {
                lastEntry: lastActivityId
            },
            function(data){
                if (data === null) {
                    return;
                }

                state.json = data;

                {% include 'js/mergeLists.js' %}

                mergeLists(state.logEntries, data.activity);

                if (state.logEntries.length > 0) {
                    lastActivityId = state.logEntries[state.logEntries.length-1].id;
                }
                updateHome();
            }
        );
    }

    that = {
        // public variables
        
        // public functions
        initialize: function () {
            Login.addStateChangeCallback(that.ajaxRequest);
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
    SCWorkbench.initialize();
});


