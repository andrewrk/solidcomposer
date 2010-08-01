var SCBandInvite = function() {
    var that;

    var templateCopyArea = "{% filter escapejs %}{% include 'workbench/invite_copy_area.jst.html' %}{% endfilter %}";
    var templateCopyAreaCompiled = null;

    var urls = {
        create_invite: "{% filter escapejs %}{% url workbench.ajax_create_invite %}{% endfilter %}",
        email_invite: "{% filter escapejs %}{% url workbench.ajax_email_invite %}{% endfilter %}"
    };

    var band_id = null;

    function compileTemplates() {
        templateCopyAreaCompiled = Jst.compile(templateCopyArea);
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
                    // put a little graphic indicating success
                    $("#invite-email .success").show().hide('slow');
                },
                'json');
            
            // clear the text box and set focus
            $("#email-box").val();
            $("#email-box").focus();
            return false;
        }
        $("#email-button").click(inviteByEmail);
        $("#email-box").keydown(function(e){
            if (e.keyCode === 13) {
                inviteByEmail();
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
