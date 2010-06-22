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

    var urls = {
        download_zip: "{% filter escapejs %}{% url workbench.download_zip %}{% endfilter %}",
        plugin: function(plugin_url) {
            return "{% filter escapejs %}{% url workbench.plugin '[~~~~]' %}{% endfilter %}".replace("[~~~~]", plugin_url);
        },
        studio: function(studio_identifier) {
            return "{% filter escapejs %}{% url workbench.studio '[~~~~]' %}{% endfilter %}".replace("[~~~~]", studio_identifier);
        }
    };

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

    var pluginTypeEnum = {
        GENERATOR: 0,
        EFFECT: 1
    };

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
        currentMp3File = null;
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

        if (currentMp3File !== null) {
            // find the dom with mp3 file
            $(".player-large .dl-mp3 a").each(function(index, element) {
                var mp3file = $(this).attr('href');
                if (mp3file === currentMp3File) {
                    currentPlayer = $(this).closest(".player-large");
                    return;
                }
            });
        }

        // downloading samples
        jdom.find(".player-large .dl-samples-dialog").dialog({
            modal: true,
            title: "Download Project Files",
            autoOpen: false
        });

        jdom.find(".player-large .dl-samples a").click(function() {
            var song_id = parseInt($(this).attr('data-songid'));
            var dialog = $("#dl-samples-dialog-"+song_id);
            dialog.dialog('open');

            var dlAll = dialog.find('.dl-all');
            dlAll.unbind('click');
            dlAll.click(function(){
                var song_id = parseInt($(this).attr('data-songid'));
                downloadZip(song_id, "");
                return false;
            });

            var dlSelected = dialog.find('.dl-selected');
            dlSelected.unbind('click');
            dlSelected.click(function(){
                var song_id = parseInt($(this).attr('data-songid'));
                var selectBox = $(this).closest(".select").find('select');
                downloadZip(song_id, selectBox.serialize());
                return false;
            });

            return false;
        });

        // dependencies
        jdom.find(".player-large .dependencies-dialog").dialog({
            modal: true,
            title: "Song Dependencies",
            autoOpen: false
        });
        jdom.find(".player-large .dependencies a").click(function() {
            var song_id = parseInt($(this).attr('data-songid'));
            var dialog = $("#dependencies-dialog-" + song_id);
            dialog.dialog('open');

            return false;
        });

        updateCurrentPlayer();
    }

    function downloadZip(song_id, samples) {
        var url = urls.download_zip + "?song=" + song_id;
        if (samples) {
            url += "&" + samples;
        }
        location.href = url;
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

    // returns true if func(element) is true for any element in list.
    function anyTrue(list, func) {
        for (var i=0; i<list.length; ++i) {
            if (func(list[i])) {
                return true;
            }
        }
        return false;
    }

    that = {
        // public variables
        onProgressChange: null,
        onSoundComplete: null,
        urls: urls,
        
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
                that.seek(0);
                that.stop();
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
        },
        // returns true if song has any available samples
        anyAvailableSamples: function(song) {
            return anyTrue(song.samples, function(sample) { return ! sample.missing; });
        },
        // returns true if song has any missing samples
        anyMissingSamples: function(song) {
            return anyTrue(song.samples, function(sample) { return sample.missing; });
        },
        anyMissingDependencies: function(song) {
            function isMissing(dep) {
                return dep.missing;
            }
            return anyTrue(song.plugins, isMissing) || song.studio.missing;
        },
        breakPluginsIntoFXAndGen: function(song) {
            song.effects = [];
            song.generators = [];
            for (var i=0; i<song.plugins.length; ++i) {
                var plugin = song.plugins[i];
                if (plugin.plugin_type === pluginTypeEnum.GENERATOR) {
                    song.generators.push(plugin);
                } else if (plugin.plugin_type === pluginTypeEnum.EFFECT) {
                    song.effects.push(plugin);
                }
            }
        },
        // used for formatting source file to display to the user.
        fileTitle: function(path) {
            var parts = path.split('/');
            if (parts.length === 0) {
                return path;
            } else {
                return parts[parts.length-1];
            }
        }
    };
    return that;
} ();
