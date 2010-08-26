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
            autoOpen: false,
            width: 400
        });
    }

    function addUiToDom(jdom) {
        jdom.find(".tip").mouseover(function(){
            var $this = $(this);
            var contentDiv = $this.next();

            tipDialog.html(contentDiv.html());
            tipDialog.dialog('open');

            // move the tip dialog to a position near the tip element
            var dialogHeight = tipDialog.parent().height();
            var dialogWidth = tipDialog.parent().width();
            var tipPos = $this.position();
            var dialogLeft, dialogTop;
            if (tipPos.top + $this.height()+dialogHeight > $(document).height()) {
                dialogTop = tipPos.top-window.pageYOffset-dialogHeight;
            } else {
                dialogTop = tipPos.top-window.pageYOffset+$this.height();
            }
            if (tipPos.left + $this.width()+dialogWidth > $(document).width()) {
                dialogLeft = tipPos.left-window.pageXOffset-dialogWidth;
            } else {
                dialogLeft = tipPos.left-window.pageXOffset+$this.width();
            }
            tipDialog.dialog('option', 'position', [dialogLeft, dialogTop]);

            function tipMouseOut() {
                tipDialog.dialog('close');
                
                $(this).unbind('mouseout', tipMouseOut);
            }

            $this.bind('mouseout', tipMouseOut);

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
