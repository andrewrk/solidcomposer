var template_available = (<r><![CDATA[{% include 'arena/available.jst.html' %}]]></r>).toString();
var template_owned = (<r><![CDATA[{% include 'arena/owned.jst.html' %}]]></r>).toString();

var template_available_s = null;
var template_owned_s = null;

var state_available = null;
var state_owned = null;

function addClicksToCompo(compo) {
    $("#compo-" + compo.id + "-remove").click(function(){
        $.ajax({
            url: "/arena/ajax/remove/" + compo.id + "/",
            type: 'GET',
            success: function(){
                ajaxRequest()
            },
            error: function(){
                ajaxRequest()
            }
        });
        return false;
    });

    $("#compo-" + compo.id + "-bookmark").click(function(){
        $.ajax({
            url: "/arena/ajax/bookmark/" + compo.id + "/",
            type: 'GET',
            success: function(){
                ajaxRequest()
            },
            error: function(){
                ajaxRequest()
            }
        });
        return false;
    });
}

function setBookmarkedProperty(data, value) {
    for(var i=0; i<data.ongoing.length; ++i)
        data.ongoing[i].bookmarked = value;

    for(var i=0; i<data.closed.length; ++i)
        data.closed[i].bookmarked = value;

    for(var i=0; i<data.upcoming.length; ++i)
        data.upcoming[i].bookmarked = value;
}

function addClicksToSection(data) {
    for(var i=0; i<data.ongoing.length; ++i)
        addClicksToCompo(data.ongoing[i]);

    for(var i=0; i<data.closed.length; ++i)
        addClicksToCompo(data.closed[i]);

    for(var i=0; i<data.upcoming.length; ++i)
        addClicksToCompo(data.upcoming[i]);
}

function updateAvailable() {
    if (state_available == null)
        return;

    $("#available").html(Jst.evaluateCompiled(template_available_s, state_available));

    addClicksToSection(state_available);
}

function updateOwned() {
    if (state_owned == null)
        return;

    $("#owned").html(Jst.evaluateCompiled(template_owned_s, state_owned));

    if (state_owned.user.is_authenticated)
        addClicksToSection(state_owned);
}

function ajaxRequest() {
    loginAjaxRequest();
    $.getJSON("/arena/ajax/available/", function(data){
        if (data == null)
            return;

        state_available = data;

        setBookmarkedProperty(state_available, false);
        updateAvailable();
    });

    $.getJSON("/arena/ajax/owned/", function(data){
        if (data == null)
            return;

        state_owned = data;
        if (data.user.is_authenticated)
            setBookmarkedProperty(state_owned, true);
        updateOwned();
    });
}

function ajaxRequestLoop() {
    ajaxRequest();
    setTimeout(ajaxRequestLoop, 10000);
}

function updateCompetitionsLoop() {
    updateAvailable();
    updateOwned();
    setTimeout(updateCompetitionsLoop, 1000);
}

function compileTemplates() {
    template_available_s = Jst.compile(template_available);
    template_owned_s = Jst.compile(template_owned);
    compileLoginTemplates();
}

$(document).ready(function(){
    compileTemplates();
    ajaxRequestLoop();
    updateCompetitionsLoop();
});

