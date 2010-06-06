var Player = function() {
    var that;

    // CSS-dependent stuff
    var waveformWidth = 800;
    var waveformHeight = 100;
    var volumeIconHeight = 24;

    // jPlayer jQuery object
    var media_url = "{{ MEDIA_URL }}";
    var jPlayerSwfPath = media_url + "swf";
    var jp = null;

    // if true, the user cannot alter playback, other than volume.
    var disabledUi = false;

    // volume is global to Player
    var volume = null;

    // the div that is the currently playing track.
    var currentPlayer = null;
    var currentMp3File = null;

    var playedTime = null;
    var totalTime = null;

    var loadPercent = null;

    // if this is not null, as soon as we get
    // onprogress, we need to seek.
    var pendingSeekPercent = null;

    var imagesToCache = [
        "img/note16.png",
        "img/dl-zip16.png",
        "img/check16.png",
        "img/warning16.png",
        "img/flp16.png",
        "img/play-circle64.png",
        "img/pause-circle64.png",
        "img/volume-bar.png",
        "img/volume24-3bar.png",
        "img/volume24-2bar.png",
        "img/volume24-1bar.png",
        "img/volume24-0bar.png",
        "img/volume24-mute.png",
        "img/play24.png"
    ];
    var cachedImages = [];
    var volumeClasses = [
        [0.75, 'bar3'],
        [0.50, 'bar2'],
        [0.25, 'bar1'],
        [0.01, 'bar0'],
        [-1, 'mute']
    ];

    var offsetTop = null;
    var volumeMouseMove = function(e) {
        e.preventDefault();

        var relativeY = e.pageY - offsetTop;
        var maxY = waveformHeight-10;
        var newVolume = 1 - (relativeY / maxY);
        that.setVolume(newVolume);
        updateVolume();
    }
    var volumeMouseUp = function(e) {
        e.preventDefault();
        $(this).unbind('mousemove', volumeMouseMove);
        $(this).unbind('mouseup', volumeMouseUp);
    }

    function onSoundComplete() {
        if (that.onSoundComplete) {
            that.onSoundComplete();
        }
    }

    function onProgressChange(_loadPercent, _playedPercentRelative,
        _playedPercentAbsolute, _playedTime, _totalTime)
    {
        playedTime = _playedTime/1000;
        totalTime = _totalTime/1000;
        loadPercent = _loadPercent/100;

        if (pendingSeekPercent) {
            that.seek(pendingSeekPercent * totalTime);
            pendingSeekPercent = null;
        }

        updateCurrentPlayer();

        if (that.onProgressChange) {
            that.onProgressChange(loadPercent, playedPercentRelative,
                playedPercentAbsolute, playedTime, totalTime);
        }
    }

    function initializeJPlayer(readyFunc) {
        var current_url;
        var actually_playing;
        
        jp = $("#jplayer");
        jp.jPlayer({
            ready: function(){
                jp.jPlayer("onSoundComplete", onSoundComplete);
                jp.jPlayer("onProgressChange", onProgressChange);

                if (readyFunc) {
                    readyFunc();
                }
            },
            swfPath: jPlayerSwfPath,
            preload: 'auto'
        });
    }

    function addUiToDom(jdom) {
        // TODO: each click function needs to identify which
        // play is getting clicked on. if it's not the current one
        // it needs to switch before doing the action.
        jdom.find(".player-large .button a").click(function(){
            if (! disabledUi) {
                var parentPlayer = $(this).closest('.player-large');
                that.setCurrentPlayer(parentPlayer);

                var isPlaying = that.isPlaying();
                if (isPlaying) {
                    that.pause();
                } else {
                    that.play();
                }
            }
            return false;
        });

        // scrubbing
        jdom.find(".player-large .wave-outer").mousedown(function(e){
            if (! disabledUi) {
                var parentPlayer = $(this).closest('.player-large');
                that.setCurrentPlayer(parentPlayer);

                var relativeX = e.pageX - this.offsetLeft;
                pendingSeekPercent = (relativeX/waveformWidth);
                that.play();
                updateCurrentPlayer();
            }
            e.preventDefault();
            return false;
        });

        // volume control
        jdom.find(".player-large .volume").mousedown(function(e){
            e.preventDefault();
            offsetTop = this.offsetTop;
            $(document).bind('mousemove', volumeMouseMove);
            $(document).bind('mouseup', volumeMouseUp);
        });

        /*jdom.find(".player-large .volume .icon").mousedown(function(e){
            e.preventDefault();
        });*/

        updateCurrentPlayer();
    }

    function updateVolume() {
        var volume = that.volume();
        var volumeClass = null;
        var i;
        for (i=0; i<volumeClasses.length; ++i) {
            if (volume >= volumeClasses[i][0]) {
                volumeClass = volumeClasses[i][1];
                break;
            }
        }
        $(".player-large .volume .icon-id")
            .attr('class', 'icon-id')
            .addClass(volumeClass);
        var maxY = waveformHeight - volumeIconHeight;
        var yPos = (1-volume) * maxY;
        $(".player-large .volume .icon").css("top", yPos);

    }

    function updateCurrentPlayer() {
        // update volume - this affects every player on the page
        updateVolume();

        // everything below affects only currentPlayer
        if (currentPlayer === null) {
            return;
        }
        
        // show the correct button image
        var isPlaying = that.isPlaying();
        var showImg = isPlaying ? 'pause' : 'play';
        var grayedClass = disabledUi ? 'disabled' : 'enabled';
        currentPlayer.find(".button span")
            .attr('class', showImg)
            .addClass(grayedClass);

        // update time and seek head
        var percent;

        // time display
        if (playedTime < 0) {
            currentPlayer.find(".time").html("Buffering... "
                + (-Math.ceil(playedTime)) + "s");
            percent = 0;
        } else {
            currentPlayer.find(".time").html(Time.timeDisplay(playedTime)
                + " / " + Time.timeDisplay(totalTime));
            percent = playedTime / totalTime;
        }

        // seek head
        var seekWidth = percent * waveformWidth;
        var waveWidth = loadPercent * waveformWidth;
        currentPlayer.find(".overlay-border").css('width', seekWidth+"px");
        currentPlayer.find(".wave").css('width', waveWidth+"px");
    }

    function cacheImages() {
        var i;
        for (i=0; i<imagesToCache.length; ++i) {
            cachedImages[i] = new Image();
            cachedImages[i].src = media_url + imagesToCache[i];
        }
    }

    that = {
        // public variables
        onProgressChange: null,
        onSoundComplete: null,
        
        // public methods
        initialize: function(readyFunc) {
            initializeJPlayer(readyFunc);
            cacheImages();
        },
        play: function() {
            jp.jPlayer("play");
            updateCurrentPlayer();
        },
        pause: function() {
            jp.jPlayer("pause");
            updateCurrentPlayer();
        },
        stop: function() {
            jp.jPlayer("stop");
            updateCurrentPlayer();
        },
        seek: function(seconds) {
            jp.jPlayer("playHeadTime", seconds*1000);
            updateCurrentPlayer();
        },
        isPlaying: function() {
            return jp.jPlayer("getData", "diag.isPlaying");
        },
        url: function() {
            return jp.jPlayer("getData", "diag.src");
        },
        setUiEnabled: function(uiEnabled) {
            disabledUi = ! uiEnabled;
            updateCurrentPlayer();
        },
        // do this one time to make the html player actually
        // be clickable by the user
        // dom is a dom element to search in. leave it out
        // to apply to the entire page.
        addUi: function(dom) {
            addUiToDom(dom ? $(dom) : $);
        },

        // use this to start playing. you send it
        // the div with class="player-large"
        // this will pre-load.
        setCurrentPlayer: function(dom) {
            // get the mp3 out of the dom
            var mp3file = $(dom).find('.dl-mp3 a').attr('href')
            if (currentMp3File === mp3file) {
                return;
            }
            if (currentPlayer !== null) {
                that.pause();
                updateCurrentPlayer();
            }
            currentPlayer = $(dom);
            currentMp3File = mp3file;
            jp.jPlayer('setFile', mp3file);
            updateCurrentPlayer();
        },

        volume: function() {
            return jp.jPlayer("getData", "volume") / 100;
        },
        // on a scale from 0.0 to 1.0
        setVolume: function(vol) {
            jp.jPlayer("volume", vol * 100);
            updateCurrentPlayer();
        }
    };
    return that;
} ();
