$(document).ready(function(){
    $(".showdown").each(function(index, item) {
        $(item).html(Showdown.instance.makeHtml($(item).html()));
    });
});
