var SCBand = function() {
    // private variables
    var that;

    var band_id;

    // configurable stuff
    var stateRequestTimeout = 60 * 1000;

    var template_filters = "{% filter escapejs %}{% include 'workbench/filters.jst.html' %}{% endfilter %}";
    var template_filters_s = null;
    var template_project_list = "{% filter escapejs %}{% include 'workbench/project_list.jst.html' %}{% endfilter %}";
    var template_project_list_s = null;

    var state = {
        urls: {
            ajax_project_filters: "{% filter escapejs %}{% url workbench.ajax_project_filters %}{% endfilter %}",
        },
        json: null
    };

    function compileTemplates() {
        template_filters_s = Jst.compile(template_filters);
        template_project_list_s = Jst.compile(template_project_list);
    }
    function ajaxRequestLoop() {
        that.ajaxRequest();
        setTimeout(ajaxRequestLoop, stateRequestTimeout);
    }
    function updateFilters() {
        $("#filters").html(Jst.evaluate(template_filters_s, state));
    }
    function ajaxRequestFilters() {
        $.getJSON(
            state.urls.ajax_project_filters,
            {
                "band": band_id
            },
            function(data){
                if (data === null) {
                    return;
                }
                if (data.success !== true) {
                    return;
                }
                state.json = data.data;
                updateFilters();
            }
        );
    }

    that = {
        // public variables
        
        // public functions
        initialize: function (_band_id) {
            band_id = _band_id;
            compileTemplates();
            ajaxRequestLoop();
        },
        
        ajaxRequest: function () {
            ajaxRequestFilters();
            // ajaxRequestProjectList();
        }
    };
    return that;
}();


$(document).ready(function(){
    Time.initialize(server_time, local_time);

    Login.initialize();
    Login.addStateChangeCallback(SCBand.ajaxRequest);

    SCBand.initialize(band_id);
});

