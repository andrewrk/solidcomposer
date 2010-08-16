var SCBandpage = function() {
    var that;

    var templateSongList = "{% filter escapejs %}{% include 'recent_userpage_songs.jst.html' %}{% endfilter %}";
    var templateSongListCompiled = null;

    var state = {};

    function compileTemplates() {
        templateSongListCompiled = Jst.compile(templateSongList);
    }

    function updateSongList() {
        $("#recent-songs").html(Jst.evaluate(templateSongListCompiled, state));
        Player.addUi("#recent-songs");
    }

    that = {
        initialize: function(recent_song_data, user_data) {
            state.user = user_data;
            state.songs = recent_song_data;

            Player.initialize();
            Player.setUser(state.user);

            compileTemplates();

            $.each(state.songs, function(index, song) {
                Player.processSong(song);
            });

            updateSongList();

        }
    };
    return that;
}();

$(document).ready(function(){
    SCBandpage.initialize(recent_song_data, user_data);
});

