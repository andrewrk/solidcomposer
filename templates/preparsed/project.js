var SCProject = function () {
    // private variables
    var that;

    // configurable stuff
    var stateRequestTimeout = 10000;

    var template_version = "{% filter escapejs %}{% include 'workbench/version.jst.html' %}{% endfilter %}";
    var template_version_s = null;

    var state = {
        urls: {
            ajax_project: "{% filter escapejs %}{% url workbench.ajax_project %}{% endfilter %}",
        },
        json: null
    };
    
    // private functions
    function updateProjects() {
        if (state.json === null) {
            return;
        }
    }

    function ajaxRequestLoop() {
        that.ajaxRequest();
        setTimeout(ajaxRequestLoop, stateRequestTimeout);
    }

    function compileTemplates() {
        template_version_s = Jst.compile(template_version);
    }

    function ajaxRequestProject() {
        $.getJSON(
            state.urls.ajax_project,
            {
                // no data to send
            },
            function(data){
                if (data === null) {
                    return;
                }

                state.json = data;
                updateProjects();
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
            ajaxRequestProject();
        }
    };
    return that;
} ();

$(document).ready(function(){
    Time.initialize(server_time, local_time);

    Login.initialize();
    Login.addStateChangeCallback(SCProject.ajaxRequest);

    SCProject.initialize();
});


