{% load jst %}

var SCArena = function () {
    // private variables
    var that;

    // configurable stuff
    var stateRequestTimeout = 10000;

    var template_available = "{% filter jst_escape %}{% include 'arena/available.jst.html' %}{% endfilter %}";
    var template_owned = "{% filter jst_escape %}{% include 'arena/owned.jst.html' %}{% endfilter %}";

    var template_available_s = null;
    var template_owned_s = null;

    var state = {
        available: null,
        owned: null,
    }
    
    // private functions
    function addClicksToCompo(compo) {
        $("#compo-" + compo.id + "-remove").click(function(){
            $.ajax({
                url: "/arena/ajax/remove/" + compo.id + "/",
                type: 'GET',
                success: function(){
                    that.ajaxRequest();
                },
                error: function(){
                    that.ajaxRequest();
                }
            });
            return false;
        });

        $("#compo-" + compo.id + "-bookmark").click(function(){
            $.ajax({
                url: "/arena/ajax/bookmark/" + compo.id + "/",
                type: 'GET',
                success: function(){
                    that.ajaxRequest();
                },
                error: function(){
                    that.ajaxRequest();
                }
            });
            return false;
        });
    }

    function setBookmarkedProperty(data, value) {
        for(var i=0; i<data.compos.length; ++i) {
            data.compos[i].bookmarked = value;
        }
    }

    function addClicksToSection(data) {
        for(var i=0; i<data.compos.length; ++i) {
            addClicksToCompo(data.compos[i]);
        }
    }

    function updateAvailable() {
        if (state.available === null) {
            return;
        }

        $("#available").html(Jst.evaluate(template_available_s, state.available));

        addClicksToSection(state.available);
    }

    function updateOwned() {
        if (state.owned === null) {
            return;
        }

        $("#owned").html(Jst.evaluate(template_owned_s, state.owned));

        if (state.owned.user.is_authenticated) {
            addClicksToSection(state.owned);
        }
    }

    function ajaxRequestLoop() {
        that.ajaxRequest();
        setTimeout(ajaxRequestLoop, stateRequestTimeout);
    }

    function updateCompetitionsLoop() {
        updateAvailable();
        updateOwned();
        setTimeout(updateCompetitionsLoop, stateRequestTimeout);
    }

    function compileTemplates() {
        template_available_s = Jst.compile(template_available);
        template_owned_s = Jst.compile(template_owned);
    }

    that = {
        // public variables
        
        // public functions
        initialize: function () {
            compileTemplates();
            ajaxRequestLoop();
            updateCompetitionsLoop();
        },
        
        ajaxRequest: function () {
            $.getJSON("/arena/ajax/available/", function(data){
                if (data === null) {
                    return;
                }

                state.available = data;

                setBookmarkedProperty(state.available, false);
                updateAvailable();
            });

            $.getJSON("/arena/ajax/owned/", function(data){
                if (data === null) {
                    return;
                }

                state.owned = data;
                if (data.user.is_authenticated) {
                    setBookmarkedProperty(state.owned, true);
                }
                updateOwned();
            });
        }
    };
    return that;
} ();

$(document).ready(function(){
    Time.initialize(server_time, local_time);

    Login.initialize();
    Login.addStateChangeCallback(SCArena.ajaxRequest);

    SCArena.initialize();
});

