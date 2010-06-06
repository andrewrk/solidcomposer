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
        urls: {% include 'workbench/urls.jst.html' %},
        filters: null,
        projects: null,
        band: null
    };

    var page = 1;
    var filter = null;
    var searchText = null;

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
    
    function updateProjectList() {
        $("#project-list").html(Jst.evaluate(template_project_list_s, state));
        Player.addUi("#project-list");
    }

    function ajaxRequestFilters() {
        $.getJSON(
            state.urls.ajax_project_filters,
            {
                band: band_id
            },
            function(data){
                if (data === null) {
                    return;
                }
                if (data.success !== true) {
                    return;
                }
                state.filters = data.data;
                updateFilters();
            }
        );
    }

    function ajaxRequestProjectList() {
        var sendData = {
            band: band_id,
            page: page,
            search: $("#search").val()
        }
        if (filter !== null) {
            sendData.filter = filter;
        }
        function respond(data) {
            if (data === null) {
                return;
            }
            if (data.success !== true) {
                return;
            }
            state.projects = data.data;
            updateProjectList();
        }
        $.getJSON(state.urls.ajax_project_list, sendData, respond);
    }

    that = {
        // public variables
        
        // public functions
        initialize: function (_band_id) {
            compileTemplates();
            band_id = _band_id;

            Player.initialize();

            ajaxRequestLoop();
        },
        
        ajaxRequest: function () {
            ajaxRequestFilters();
            ajaxRequestProjectList();
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

