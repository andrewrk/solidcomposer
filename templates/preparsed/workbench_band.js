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
    var searchTextActive = false;

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
        var searchText = searchTextActive ? $("#search").val() : "";
        var sendData = {
            band: band_id,
            page: page,
            search: searchText
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

            for (var i=0; i<state.projects.projects.length; ++i) {
                Player.processSong(state.projects.projects[i].latest_version.song);
            }

            updateProjectList();
        }
        $.getJSON(state.urls.ajax_project_list, sendData, respond);
    }

    function addStaticClicks() {
        $("#search").keydown(function(e) {
            if (e.keyCode === 13) {
                ajaxRequestProjectList();
                
                e.preventDefault();
                return false;
            }
        });
        $("#search").focus(function(e) {
            if (! searchTextActive) {
                $(this).val("");
                $(this).attr('class', 'active');
                searchTextActive = true;
            }
        });
    }

    that = {
        // public variables
        
        // public functions
        initialize: function (_band_id) {
            compileTemplates();
            band_id = _band_id;

            addStaticClicks();
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

