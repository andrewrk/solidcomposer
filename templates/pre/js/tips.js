var SCTips = function() {
    var that;

    var tipDialog = null;

    function initializeDialogs() {
        $('body').prepend('<div id="tip-dialog" style="display: none;"></div>');
        tipDialog = $('#tip-dialog');
        tipDialog.dialog({
            modal: false,
            closeOnEscape: true,
            title: "Tip",
            autoOpen: false
        });
    }

    function addUiToDom(jdom) {
        jdom.find(".tip").mouseover(function(){
            var contentDiv = $(this).next();

            tipDialog.html(contentDiv.html());
            tipDialog.dialog('open');

            function tipMouseOut() {
                tipDialog.dialog('close');
                
                $(this).unbind('mouseout', tipMouseOut);
            }

            $(this).bind('mouseout', tipMouseOut);

            return false;
        });
        jdom.find('.tip').click(function(){
            return false;
        });
    }

    that = {
        initialize: function() {
            initializeDialogs();
            addUiToDom($('body'));
        },
        addUi: function(dom) {
            addUiToDom($(dom));
        }
    };
    return that;
}();

$(document).ready(SCTips.initialize);
