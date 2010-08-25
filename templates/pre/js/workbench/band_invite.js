var SCBandInvite = function() {
    var that;

    var templateCopyArea = "{% filter escapejs %}{% include 'workbench/band/invite_copy_area.jst.html' %}{% endfilter %}";
    var templateCopyAreaCompiled = null;

    var urls = {
        create_invite: "{% filter escapejs %}{% url workbench.ajax_create_invite %}{% endfilter %}",
        email_invite: "{% filter escapejs %}{% url workbench.ajax_email_invite %}{% endfilter %}",
        username_invite: "{% filter escapejs %}{% url workbench.ajax_username_invite %}{% endfilter %}"
    };

    var band_id = null;

    function compileTemplates() {
        templateCopyAreaCompiled = Jst.compile(templateCopyArea);
    }

    function showSuccess(dom) {
        // put a little graphic indicating success
        $(dom).show();
        function hideIt(){
            $(dom).hide('slow');
        }
        setTimeout(hideIt, 2000);
    }

    function addClicks() {
        function makeShowFunction(divId) {
            return function() {
                $("#" + divId + " .dropdown").show('fast');
                return false;
            }
        }
        function makeHideFunction(divId) {
            return function() {
                $("#" + divId + " .dropdown").hide('fast');
                return false;
            }
        }
        var divs = ['invite-link', 'invite-email', 'invite-local'];
        $.each(divs, function(index, div) {
            $("#" + div + " h1 a").toggle(makeShowFunction(div), makeHideFunction(div));
        });

        $("#invite-link h1 a").click(function(){
            // create url from server
            $.post(
                urls.create_invite,
                {
                    band: band_id
                },
                function(data) {
                    if (! data.success) {
                        alert("Error creating invitation link: " + data.reason);
                        return;
                    }
                    $("#copy-area").html(Jst.evaluate(templateCopyAreaCompiled, {url: data.data.url}));
                    SCTips.addUi("#copy-area");

                    function selectAll() {
                        this.select();
                    }
                    $("#copy-area input").focus(selectAll).click(selectAll);
                },
                'json');
        });

        function inviteByEmail() {
            // post the invitation
            $.post(
                urls.email_invite,
                {
                    band: band_id,
                    email: $("#email-box").val()
                },
                function (data) {
                    if (! data.success) {
                        alert("Error sending invitation: " + data.reason);
                        return;
                    }
                    showSuccess("#invite-email .success");

                    // clear the text box and set focus
                    $("#email-box").val('');
                    $("#email-box").focus();

                },
                'json');
            
            return false;
        }
        $("#email-button").click(inviteByEmail);
        $("#email-box").keydown(function(e){
            if (e.keyCode === 13) {
                inviteByEmail();
                return false;
            }
        });

        function inviteByUsername() {
            // post the invitation
            $.post(
                urls.username_invite,
                {
                    band: band_id,
                    username: $("#local-box").val()
                },
                function (data) {
                    if (! data.success) {
                        alert("Error sending invitation: " + data.reason);
                        return;
                    }
                    showSuccess("#invite-local .success");

                    // clear the text box and set focus
                    $("#local-box").val('');
                    $("#local-box").focus();
                },
                'json');
            
            return false;
        }
        $("#local-button").click(inviteByUsername);
        $("#local-box").keydown(function(e){
            if (e.keyCode === 13) {
                inviteByUsername();
                return false;
            }
        });
    }

    that = {
        initialize: function(_band_id) {
            band_id = _band_id;
            compileTemplates();
            addClicks();
        }
    };
    return that;
}();
$(document).ready(function() {
    SCBandInvite.initialize(band_id);
});
