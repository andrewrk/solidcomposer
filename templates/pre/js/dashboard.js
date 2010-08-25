var SCDashboard = function() {
    var that;

    var templateCompoList = "{% filter escapejs %}{% include 'arena/compo_list.jst.html' %}{% endfilter %}";
    var templateCompoListCompiled = null;

    var templateBandActivity = "{% filter escapejs %}{% include 'workbench/recent_activity.jst.html' %}{% endfilter %}";
    var templateBandActivityCompiled = null;

    var state = {
        urls: {
            project: function(id, band_id) {
                return "{% filter escapejs %}{% url workbench.project 0 1 %}{% endfilter %}".replace("0",
                    "[~~band_id~~]").replace("1", id).replace("[~~band_id~~]", band_id);
            },
            project_version: function(project_id, band_id, version_number) {
                return this.project(project_id, band_id) + "#version" + version_number;
            },
            band: function(id) {
                return "{% filter escapejs %}{% url workbench.band 0 %}{% endfilter %}".replace(0, id);
            },
            userpage: function (username) {
                return "{% filter escapejs %}{% url userpage '[~~~~]' %}{% endfilter %}".replace("[~~~~]", username);
            },
            ajax_activity: "{% filter escapejs %}{% url workbench.ajax_activity %}{% endfilter %}",
            ajax_owned: "{% filter escapejs %}{% url arena.ajax_owned %}{% endfilter %}",
            compete: function (id) {
                return "{% filter escapejs %}{% url arena.compete 0 %}{% endfilter %}".replace(0, id);
            }
        },
        user: null,
        logEntries: [],
        entryTypeEnum: {% include 'workbench/entryTypeEnum.jst.html' %},
        compo_list: null,
        list_name: 'dashboard'
    };

    var lastActivityId = null;

    function compileTemplates() {
        templateCompoListCompiled = Jst.compile(templateCompoList);
        templateBandActivityCompiled = Jst.compile(templateBandActivity);
    }

    function updateActivity() {
        if (state.user === null) {
            return;
        }
        $("#activity").html(Jst.evaluate(templateBandActivityCompiled, state));
    }

    function updateCompos() {
        $("#compos").html(Jst.evaluate(templateCompoListCompiled, state));
    }

    function ajaxRequestActivity() {
        $.getJSON(
            state.urls.ajax_activity,
            {
                lastEntry: lastActivityId
            },
            function(data){
                if (data === null) {
                    return;
                }

                {% include 'js/mergeLists.js' %}

                mergeLists(state.logEntries, data.data);

                if (state.logEntries.length > 0) {
                    lastActivityId = state.logEntries[state.logEntries.length-1].id;
                }
                updateActivity();
            }
        );
    }

    function ajaxRequestCompos() {
        $.getJSON(
            state.urls.ajax_owned,
            {},
            function(data){
                if (data === null) {
                    return;
                }

                state.compo_list = data;
                // hax!
                state.compo_list.page_count = 1
                state.compo_list.page_number = 1

                updateCompos();
            }
        );
    }

    function ajaxRequest() {
        ajaxRequestActivity();
        ajaxRequestCompos();
    }

    function ajaxRequestLoop() {
        ajaxRequest();
        setTimeout(ajaxRequest, 20000);
    }

    function loginStateChangeCallback(user) {
        state.user = user;
        ajaxRequest();
    }

    that = {
        initialize: function() {
            Login.addStateChangeCallback(loginStateChangeCallback);
            Login.getUser(loginStateChangeCallback);
            compileTemplates();
            ajaxRequestLoop();
        }
    };
    return that;
}();

$(document).ready(SCDashboard.initialize);
