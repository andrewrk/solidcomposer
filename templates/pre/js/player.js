/*  Requires that you call Player.processSong(song) for each song data
 *  structure that you want the player to use.
 *  After you generate the dom for the player, run Player.addUiToDom(dom) on it.
 *  At this point, Player takes care of the rest!
 */

var Player = function() {
    var that;

    var templateDepsDialog = "{% filter escapejs %}{% include 'player_deps_dialog.jst.html' %}{% endfilter %}";
    var templateDepsDialogCompiled = null;

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
        },
        dependency_ownership: "{% filter escapejs %}{% url workbench.ajax_dependency_ownership %}{% endfilter %}",
        userpage: function (username) {
            return "{% filter escapejs %}{% url userpage '[~~~~]' %}{% endfilter %}".replace("[~~~~]", username);
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
        EFFECT: 1,
        STUDIO: 2
    };

    // keep track of all the songs
    var songs = {};

    var updateCallback = null;

    var volumeOffsetTop = null;
    var volumeStartY = null;
    var volumeStartValue = null;
    var volumeMouseMove = function(e) {
        e.preventDefault();

        var relativeY = e.pageY - volumeOffsetTop;
        var deltaY = relativeY - volumeStartY;
        var deltaVolume = -deltaY / that.waveformHeight;
        var newVolume = volumeStartValue + deltaVolume;
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
                pendingSeekPercent = (relativeX/that.waveformWidth);
                that.play();
                updateCurrentPlayer();
            }
            e.preventDefault();
            return false;
        });

        // volume control
        jdom.find(".player-large .volume").mousedown(function(e){
            e.preventDefault();
            volumeOffsetTop = this.offsetTop;
            volumeStartY = e.pageY - volumeOffsetTop;
            volumeStartValue = that.volume();
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
        jdom.find(".player-large .dl-samples-dialog").remove();
        jdom.find(".player-large .dl-samples-dialog-init")
            .dialog({
                modal: true,
                title: "Download Project Files",
                autoOpen: false,
                maxWidth: 400,
                maxHeight: 500
            })
            .attr('class', 'dl-samples-dialog');

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
        jdom.find(".player-large .dependencies-dialog").remove();
        jdom.find(".player-large .dependencies-dialog-init")
            .dialog({
                modal: true,
                title: "Song Dependencies",
                autoOpen: false,
                maxWidth: 400,
                maxHeight: 500
            })
            .attr('class', 'dependencies-dialog');

        jdom.find(".player-large .dependencies a").click(function() {
            var song_id = parseInt($(this).attr('data-songid'));
            var dialog = $("#dependencies-dialog-" + song_id);
            dialog.dialog('open');

            addUiToDependencyDialog(dialog, songs[song_id]);

            return false;
        });

        updateCurrentPlayer();
    }

    function addUiToDependencyDialog(dialog, song) {
        var donothaves = dialog.find('.donothave');
        donothaves.unbind('click');
        donothaves.click(function(){
            var dependency_id = parseInt($(this).parent().attr('data-dependencyid'));
            var plugin_type = parseInt($(this).parent().attr('data-plugintype'));
            $.post(urls.dependency_ownership, {
                dependency_id: dependency_id,
                dependency_type: plugin_type
            }, function(data) {
                if (data === null) {
                    return;
                }
                if (! data.success) {
                    return;
                }

                if (plugin_type === pluginTypeEnum.STUDIO) {
                    song.studio.missing = true;
                } else {
                    song.pluginLink[dependency_id].missing = true;
                }

                that.processSong(song);

                // re-render the dialog
                dialog.html(Jst.evaluate(templateDepsDialogCompiled, {song: song}));
                addUiToDependencyDialog(dialog, song);

                updateCallback();
            }, 'json');
            return false;
        });

        var haves = dialog.find('.have');
        haves.unbind('click');
        haves.click(function(){
            var dependency_id = parseInt($(this).parent().attr('data-dependencyid'));
            var plugin_type = parseInt($(this).parent().attr('data-plugintype'));

            $.post(urls.dependency_ownership, {
                dependency_id: dependency_id,
                dependency_type: plugin_type,
                have: true
            }, function(data) {
                if (data === null) {
                    return;
                }
                if (! data.success) {
                    return;
                }
                // replace the have link with the do not have link
                if (plugin_type === pluginTypeEnum.STUDIO) {
                    song.studio.missing = false;
                } else {
                    song.pluginLink[dependency_id].missing = false;
                }

                that.processSong(song);

                // re-render the dialog
                dialog.html(Jst.evaluate(templateDepsDialogCompiled, {song: song}));
                addUiToDependencyDialog(dialog, song);

                updateCallback();
            }, 'json');

            return false;
        });
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
        var maxY = that.waveformHeight - that.volumeIconHeight;
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
        var seekWidth = percent * that.waveformWidth;
        var waveWidth = loadPercent * that.waveformWidth;
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

    function compileTemplates() {
        templateDepsDialogCompiled = Jst.compile(templateDepsDialog);
    }

    function processCommentNode(song, comment_node) {
        for (var i=0; i<comment_node.children.length; ++i) {
            var node = comment_node.children[i];
            if (node.position !== null) {
                song.timed_comments.push(node);
            }
            processCommentNode(song, node);
        }
    }

    that = {
        // public variables
        onProgressChange: null,
        onSoundComplete: null,
        urls: urls,
        pluginTypeEnum: pluginTypeEnum,

        // CSS-dependent stuff
        waveformWidth: 800,
        waveformHeight: 100,
        volumeIconHeight: 24,
        timedCommentSize: 24,
        
        // public methods
        initialize: function(readyFunc, _updateCallback) {
            updateCallback = _updateCallback;
            compileTemplates();
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
        processSong: function(song) {
            // sneaky, sneaky!
            songs[song.id] = song;

            if (song.studio) {
                song.anyAvailableSamples = anyTrue(song.samples, function(sample){
                    return ! sample.missing;
                });
                song.anyMissingSamples = anyTrue(song.samples, function(sample){
                    return sample.missing;
                });
                song.anyMissingDependencies = song.studio.missing || anyTrue(song.plugins, function(plugin){
                    return plugin.missing;
                });

                song.effects = [];
                song.generators = [];
                // plugin id -> plugin variable
                song.pluginLink = {};
                for (var i=0; i<song.plugins.length; ++i) {
                    var plugin = song.plugins[i];
                    song.pluginLink[plugin.id] = plugin;
                    if (plugin.plugin_type === pluginTypeEnum.GENERATOR) {
                        song.generators.push(plugin);
                    } else if (plugin.plugin_type === pluginTypeEnum.EFFECT) {
                        song.effects.push(plugin);
                    }
                }
            }

            // create a list of timed comments
            song.timed_comments = []
            processCommentNode(song, song.comment_node);
            song.timed_comments.sort(function(a,b){
                return a.position - b.position;
            });
        },
        // used for formatting source file to display to the user.
        fileTitle: function(path) {
            var parts = path.split('/');
            if (parts.length === 0) {
                return path;
            } else {
                return parts[parts.length-1];
            }
        },
        formatCurrency: function(amt) {
            return amt.toFixed(2);
        }
    };
    return that;
} ();
