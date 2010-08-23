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
    var template_spacemeter = "{% filter escapejs %}{% include 'workbench/band/spacemeter.jst.html' %}{% endfilter %}";
    var template_spacemeter_s = null;
    var template_space_warning = "{% filter escapejs %}{% include 'workbench/space_warning.jst.html' %}{% endfilter %}";
    var template_space_warning_s = null;

    var state = {
        urls: {% include 'workbench/urls.jst.html' %},
        filters: null,
        projects: null,
        band: null,
        user: null
    };

    var page = 1;
    var filter = null;
    var searchTextActive = false;

    function anchor() {
        var parts = location.href.split('#');
        if (parts.length > 1) {
            return parts[parts.length-1];
        }
        return "";
    }

    function activeFilter() {
        return anchor() || "all";
    }

    function compileTemplates() {
        template_filters_s = Jst.compile(template_filters);
        template_project_list_s = Jst.compile(template_project_list);
        template_spacemeter_s = Jst.compile(template_spacemeter);
        template_space_warning_s = Jst.compile(template_space_warning);
    }

    function ajaxRequestLoop() {
        that.ajaxRequest();
        setTimeout(ajaxRequestLoop, stateRequestTimeout);
    }

    function updateFilters() {
        $("#filters").html(Jst.evaluate(template_filters_s, state));
        SCTips.addUi("#filters");

        $(".filter").parent().attr('class', 'unselected');
        $("#filter-" + activeFilter()).attr('class', 'selected');

        $(".filter").click(function(){
            filter = $(this).attr('data-filterid');
            $(".filter").parent().attr('class', 'unselected');
            $(this).parent().attr('class', 'selected');
            ajaxRequestProjectList();

            // we want the anchor to go into the url
            return true;
        });
    }
    
    function updateProjectList() {
        if (state.user === null || state.projects === null) {
            return;
        }
        $("#project-list").html(Jst.evaluate(template_project_list_s, state));
        Player.addUi("#project-list");
        SCTips.addUi("#project-list");

        $("#space-warning").html(Jst.evaluate(template_space_warning_s, state));
        if (state.band.used_space > state.band.total_space) {
            $("#space-warning").show();
        } else {
            $("#space-warning").hide();
        }

        // page navigation
        $(".nav a").click(function(){
            page = $(this).attr('data-page');
            ajaxRequestProjectList();
            return false;
        });
    }

    function updateSpaceMeter() {
        if (state.band === null) {
            return;
        }
        $("#band-spacemeter").html(Jst.evaluate(template_spacemeter_s, state));
        SCTips.addUi("#band-spacemeter");
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
            state.band = data.data.band;

            for (var i=0; i<state.projects.projects.length; ++i) {
                Player.processSong(state.projects.projects[i].latest_version.song);
            }

            updateProjectList();
            updateSpaceMeter();
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
            Login.addStateChangeCallback(that.ajaxRequest);

            compileTemplates();
            band_id = _band_id;

            addStaticClicks();
            Player.initialize(null, updateProjectList);

            filter = activeFilter();
            ajaxRequestLoop();
        },
        
        ajaxRequest: function () {
            ajaxRequestFilters();
            ajaxRequestProjectList();
            Login.getUser(function(user){
                state.user = user;
                updateProjectList();
            });
        }
    };
    return that;
}();


$(document).ready(function(){
    SCBand.initialize(band_id);
});

