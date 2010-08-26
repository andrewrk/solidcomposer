$(document).ready(function(){
    $(".showdown").each(function(index, item) {
        $(item).html(Showdown.makeHtml($(item).html()));
    });
});
