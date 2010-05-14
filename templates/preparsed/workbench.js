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
        },
        json: null
    }
    
    // private functions
    function updateHome() {
        if (state.json === null) {
            return;
        }

        $("#workbench").html(Jst.evaluate(template_home_s, state));
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


