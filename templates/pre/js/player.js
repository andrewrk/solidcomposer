/*  Requires that you call Player.processSong(song) for each song data
 *      structure that you want the player to use.
 *  Call Player.setUser() as soon as you have user data.
 *  After you generate the dom for the player, run Player.addUiToDom(dom) on it.
 *  At this point, Player takes care of the rest!
 */

var Player = function() {
    var that;

    var templateDepsDialog = "{% filter escapejs %}{% include 'player/deps_dialog.jst.html' %}{% endfilter %}";
    var templateDepsDialogCompiled = null;

    var templateSamplesDialog = "{% filter escapejs %}{% include 'player/dl_samples_dialog.jst.html' %}{% endfilter %}";
    var templateSamplesDialogCompiled = null;

    var templateCommentDialog = "{% filter escapejs %}{% include 'player/comment_dialog.jst.html' %}{% endfilter %}";
    var templateCommentDialogCompiled = null;

    var templateCommentTip = "{% filter escapejs %}{% include 'player/comment_tip_dialog.jst.html' %}{% endfilter %}";
    var templateCommentTipCompiled = null;

    var templateInsertComment = "{% filter escapejs %}{% include 'player/insert_timed_comment.jst.html' %}{% endfilter %}";
    var templateInsertCommentCompiled = null;

    var media_url = "{{ MEDIA_URL }}";
    var jPlayerSwfPath = media_url + "swf";
    var jp = null; // jPlayer jQuery object

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
        },
        ajax_comment: "{% filter escapejs %}{% url ajax_comment %}{% endfilter %}"
    };

    // if true, the user cannot alter playback, other than volume.
    var disabledUi = false;

    // volume is global to Player
    var volume = null;

    // the div that is the currently playing track.
    var currentPlayer = null;
    var currentSong = null;
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

    // CSS-dependent stuff
    var waveformWidth = {{ WAVEFORM_WIDTH }};
    var waveformHeight = {{ WAVEFORM_HEIGHT }};
    var volumeIconHeight = {{ VOLUME_ICON_SIZE }};
    var timedCommentSize = {{ TIMED_COMMENT_SIZE }};

    // keep track of all the songs
    var songs = {};

    // keep track of all the comments
    var comments = {};

    // the user object
    var user = {
        is_authenticated: false,
        id: 0
    };

    var updateCallback = null;

    var dialogDownloadSamples = null;
    var dialogDependencies = null;

    var dialogInsertCommentTip = null;
    var dialogInsertCommentTipWidth = 220;
    var dialogInsertCommentTipHeight = 34;

    var dialogComment = null;
    var dialogCommentWidth = 400;
    var dialogCommentHeight = 300;
    var lastDialogComment = null;
    var dialogCommentRect = null;

    var dialogInsertComment = null;
    var dialogInsertCommentWidth = 300;
    var dialogInsertCommentHeight = 200;

    var highestZIndex = 2;

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
        loadPercent = _loadPercent/100;
        // if the song is not completely loaded, we override the length with what
        // we know it to be.
        if (loadPercent >= 1.0) {
            totalTime = _totalTime/1000;
        } else {
            totalTime = currentSong.length;
        }

        if (pendingSeekPercent) {
            that.seek(pendingSeekPercent * totalTime);
            pendingSeekPercent = null;
        }

        updateCurrentPlayer();

        if (currentSong.comments_visible) {
            // show the latest comment in time range commentLingerTime
            var commentLingerTime = 8; // seconds
            var selectedComment = null;
            var i;
            for (i=0; i<currentSong.timed_comments.length; ++i) {
                comment = currentSong.timed_comments[i];
                if (playedTime >= comment.position && playedTime < comment.position + commentLingerTime) {
                    selectedComment = comment;
                }
            }
            if (selectedComment === null) {
                hideCommentDialog();
            } else {
                showCommentDialog(selectedComment, currentPlayer, true);
            }
        }

        if (that.onProgressChange) {
            that.onProgressChange(loadPercent, playedPercentRelative,
                playedPercentAbsolute, playedTime, totalTime);
        }
    }

    function initializeJPlayer(readyFunc) {
        var current_url;
        var actually_playing;
        
        $('body').prepend("<div id=\"jplayer\"></div>");
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

    function hideCommentDialog() {
        lastDialogComment = null;
        dialogComment.dialog('close');
    }

    function checkHideComment(e){
        // how far away does it have to be to hide?
        var closeDistance = 100;
        var close = e.pageX > dialogCommentRect.right + closeDistance ||
            e.pageX < dialogCommentRect.left - closeDistance ||
            e.pageY > dialogCommentRect.bottom + closeDistance ||
            e.pageY < dialogComment.top - closeDistance;

        if (close) {
            hideCommentDialog();
            $(document).unbind('mousemove', checkHideComment);
        }
    }

    function showCommentDialog(node, playerDom, sticky) {
        if (node === lastDialogComment) {
            return;
        }
        if (node === null) {
            hideCommentDialog();
            return;
        }
        // in case we have a leftover hook
        $(document).unbind('mousemove', checkHideComment);

        lastDialogComment = node;
        var song = songs[node.song];
        var ol = $(playerDom).find('.timed-comments ol');
        var x = ol.get(0).offsetLeft + (node.position / song.length) * waveformWidth;
        var y = ol.position().top - $(document).scrollTop();
        dialogComment.html(Jst.evaluate(templateCommentDialogCompiled, {
            comment_node: node,
            user: user
        }));
        dialogComment.dialog('open');
        dialogComment.dialog('option', 'title', "{{ STR_COMMENT_DIALOG_TITLE }}" + Time.timeDisplay(node.position));
        dialogComment.dialog('option', 'position', [x, y - dialogCommentHeight - 10]);
        dialogCommentRect = {
            left: x,
            top: y,
            right: x+dialogCommentWidth,
            bottom: y+dialogCommentHeight
        };

        if (! sticky) {
            // install a hook to hide the comment box when the mouse goes too far away
            $(document).bind('mousemove', checkHideComment);
        }

    }

    function insertTimedComment(node) {
        comments[node.id] = node;

        // insert into correct position
        var i;
        var song = songs[node.song];
        for (i=0; i<song.timed_comments.length; ++i) {
            var timedComment = song.timed_comments[i];
            if (node.position < timedComment.position) {
                song.timed_comments.splice(i, 0, node);
                updateCallback();
                return;
            }
        }
        song.timed_comments.push(node);
        updateCallback();
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
        var waveOffsetLeft = null;
        var scrubMouseMove = function(e) {
            var relativeX = e.pageX - waveOffsetLeft;
            pendingSeekPercent = relativeX/waveformWidth;
            that.play();
            updateCurrentPlayer();
            e.preventDefault();
            return false;
        }

        var scrubMouseUp = function(e) {
            $(this).unbind('mousemove', scrubMouseMove);
            $(this).unbind('mouseup', scrubMouseUp);
            e.preventDefault();
            return false;
        }

        jdom.find(".player-large .wave-outer").mousedown(function(e){
            if (e.button === 0) {
                if (! disabledUi) {
                    var parentPlayer = $(this).closest('.player-large');
                    that.setCurrentPlayer(parentPlayer);

                    waveOffsetLeft = this.offsetLeft;

                    $(document).bind('mousemove', scrubMouseMove);
                    $(document).bind('mouseup', scrubMouseUp);

                    scrubMouseMove(e);
                }
            }
            e.preventDefault();
            return false;
        });

        // volume control
        var volumeOffsetTop = null;
        var volumeStartY = null;
        var volumeStartValue = null;
        var volumeMouseMove = function(e) {
            var relativeY = e.pageY - volumeOffsetTop;
            var deltaY = relativeY - volumeStartY;
            var deltaVolume = -deltaY / waveformHeight;
            var newVolume = volumeStartValue + deltaVolume;
            that.setVolume(newVolume);
            updateVolume();

            e.preventDefault();
            return false;
        }

        var volumeMouseUp = function(e) {
            $(this).unbind('mousemove', volumeMouseMove);
            $(this).unbind('mouseup', volumeMouseUp);
            e.preventDefault();
            return false;
        }
        jdom.find(".player-large .volume").mousedown(function(e){
            if (e.button === 0) {
                volumeOffsetTop = this.offsetTop;
                volumeStartY = e.pageY - volumeOffsetTop;
                volumeStartValue = that.volume();
                $(document).bind('mousemove', volumeMouseMove);
                $(document).bind('mouseup', volumeMouseUp);
            }

            e.preventDefault();
            return false;
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
        jdom.find(".player-large .dl-samples a").click(function() {
            var song_id = parseInt($(this).attr('data-songid'));
            var song = songs[song_id];

            // add content to the dialog
            dialogDownloadSamples.html(Jst.evaluate(templateSamplesDialogCompiled, {song: song}));
            dialogDownloadSamples.dialog('open');

            var dlAll = dialogDownloadSamples.find('.dl-all');
            dlAll.unbind('click');
            dlAll.click(function(){
                var song_id = parseInt($(this).attr('data-songid'));
                downloadZip(song_id, "");
                return false;
            });

            var dlSelected = dialogDownloadSamples.find('.dl-selected');
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
        jdom.find(".player-large .dependencies a").click(function() {
            var song_id = parseInt($(this).attr('data-songid'));
            var song = songs[song_id];

            // add content to the dialog
            dialogDependencies.html(Jst.evaluate(templateDepsDialogCompiled, {song: song}));
            dialogDependencies.dialog('open');

            addUiToDependencyDialog(dialogDependencies, song);

            return false;
        });

        // clicking on comments
        jdom.find('.player-large .timed-comments li a').mouseover(function(e){
            e.preventDefault();
            var comment_id = parseInt($(this).attr('data-commentid'));
            showCommentDialog(comments[comment_id], $(this).closest('.player-large'), false);
            ++highestZIndex;
            $(this).closest('li').css('z-index', highestZIndex);
            return false;
        });

        jdom.find('.player-large .timed-comments li a').click(function(e){
            e.preventDefault();
            var comment_id = parseInt($(this).attr('data-commentid'));
            showCommentDialog(comments[comment_id], $(this).closest('.player-large'), true);
            return false;
        });

        // clicking to add comments
        var commentSong = null;
        function newTipPos(offsetLeft, dialogTop, pageX) {
            var relativeX = pageX - offsetLeft;
            var percent = relativeX / waveformWidth;
            var position = percent * commentSong.length;

            if (position < commentSong.length) {
                dialogInsertCommentTip.dialog('open');
                // edit the dialog
                dialogInsertCommentTip.html(Jst.evaluate(templateCommentTipCompiled, {position: position}));
                dialogInsertCommentTip.dialog('option', 'position', [pageX - dialogInsertCommentTipWidth/2, dialogTop-dialogInsertCommentTipHeight-10]);
                return true;
            } else {
                dialogInsertCommentTip.dialog('close');
                return false;
            }
        }

        var commentBarMouseMove = function(e) {
            var y = $(this).position().top - $(document).scrollTop();
            newTipPos(this.offsetLeft, y, e.pageX);
            e.preventDefault();
            return false;
        };
        var commentBarMouseDown = function(e) {
            var commentSong = songs[parseInt($(this).closest('.player-large').attr('data-songid'))];
            var relativeX = e.pageX - this.offsetLeft;
            var percent = relativeX / waveformWidth;
            var position = percent * commentSong.length;

            // fill with correct content
            dialogInsertComment.html(Jst.evaluate(templateInsertCommentCompiled, {position: position}));
            dialogInsertComment.find('.submit input').click(function() {
                // create the comment
                var content = $('#insert-comment-dialog textarea').val();
                $.post(
                    urls.ajax_comment,
                    {
                        parent: commentSong.comment_node.id,
                        position: position,
                        content: content,
                    },
                    function(data) {
                        if (data === null ) {
                            alert("Error posting comment.");
                            return;
                        }
                        if (! data.success) {
                            alert("Error posting comment: " + data.reason);
                            return;
                        }
                        // locally insert the new comment
                        insertTimedComment(data.data);
                    },
                    'json');
                // hide the dialog
                dialogInsertComment.dialog('close');
            });

            dialogInsertComment.dialog('option', 'title', "Insert Comment at " + Time.timeDisplay(position));
            dialogInsertComment.dialog('open');
            // set focus to the text area
            $("#insert-comment-dialog textarea").focus();

            // move to correct location
            var x = e.pageX;
            var y = $(this).position().top - $(document).scrollTop();
            dialogInsertComment.dialog('option', 'position', [x, y]);

            return false;
        };
        var commentBarMouseOut = function(e) {
            $(this).unbind('mousemove', commentBarMouseMove);
            $(this).unbind('mouseout', commentBarMouseOut);
            $(this).unbind('mousedown', commentBarMouseDown);

            dialogInsertCommentTip.dialog('close');

            commentSong = null;

            e.preventDefault();
            return false;
        };
        jdom.find(".player-large .timed-comments ol").mouseover(function(e) {
            var song_id = parseInt($(this).attr('data-songid'));
            commentSong = songs[song_id];

            // show the click to add comment dialog
            dialogInsertCommentTip.dialog('open');

            var y = $(this).position().top - $(document).scrollTop();
            var preventDefault = newTipPos(this.offsetLeft, y, e.pageX);
            if (preventDefault) {
                $(this).bind('mousemove', commentBarMouseMove);
                $(this).bind('mouseout', commentBarMouseOut);
                $(this).bind('mousedown', commentBarMouseDown);

                e.preventDefault();
                return false;
            } else {
                return true;
            }
        });

        // turning comments on and off
        jdom.find(".player-large a.toggle-comments").click(function() {
            var song_id = parseInt($(this).attr('data-songid'));
            var song = songs[song_id];
            song.comments_visible = ! song.comments_visible;
            if (song === currentSong) {
                hideCommentDialog();
            }
            updateCallback();
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

    function compileTemplates() {
        templateDepsDialogCompiled = Jst.compile(templateDepsDialog);
        templateSamplesDialogCompiled = Jst.compile(templateSamplesDialog);
        templateCommentDialogCompiled = Jst.compile(templateCommentDialog);
        templateCommentTipCompiled = Jst.compile(templateCommentTip);
        templateInsertCommentCompiled = Jst.compile(templateInsertComment);
    }

    function processCommentNode(song, comment_node) {
        comments[comment_node.id] = comment_node;

        // sort the children
        comment_node.children.sort(function(a,b){
            return a.id - b.id;
        });

        // process the children
        for (var i=0; i<comment_node.children.length; ++i) {
            var node = comment_node.children[i];
            if (node.position !== null) {
                song.timed_comments.push(node);
            }
            processCommentNode(song, node);
        }
    }

    function createDialogs() {
        // insert comment tip
        $('body').prepend('<div id="comment-tip-dialog" style="display: none;"></div>');
        dialogInsertCommentTip = $('#comment-tip-dialog');
        dialogInsertCommentTip.dialog({
            modal: false,
            closeOnEscape: false,
            title: "",
            autoOpen: false,
            width: dialogInsertCommentTipWidth,
            height: dialogInsertCommentTipHeight
        });
        
        // every dialog above this has no title bar.
        $(".ui-dialog-titlebar").hide();

        // download samples
        $('body').prepend('<div id="dl-samples-dialog" style="display: none;"></div>');
        dialogDownloadSamples = $('#dl-samples-dialog');
        dialogDownloadSamples.dialog({
            modal: true,
            closeOnEscape: true,
            title: "{{ STR_SAMPLES_DIALOG_TITLE }}",
            autoOpen: false,
            maxWidth: 400,
            maxHeight: 500
        });

        // dependencies
        $('body').prepend('<div id="dependencies-dialog" style="display: none;"></div>');
        dialogDependencies = $('#dependencies-dialog');
        dialogDependencies.dialog({
            modal: true,
            title: "{{ STR_DEPS_DIALOG_TITLE }}",
            autoOpen: false,
            maxWidth: 400,
            maxHeight: 500
        });

        // comment dialog
        $('body').prepend('<div id="comment-dialog" style="display: none;"></div>');
        dialogComment = $('#comment-dialog');
        dialogComment.dialog({
            modal: false,
            closeOnEscape: true,
            title: "",
            autoOpen: false,
            width: dialogCommentWidth,
            height: dialogCommentHeight
        });
        dialogComment.bind('dialogclose', function(event, ui) {
            lastDialogComment = null;
        });

        // insert comment dialog
        $('body').prepend('<div id="insert-comment-dialog" style="display: none;"></div>');
        dialogInsertComment = $('#insert-comment-dialog');
        dialogInsertComment.dialog({
            modal: false,
            closeOnEscape: true,
            title: "",
            autoOpen: false,
            width: dialogInsertCommentWidth,
            height: dialogInsertCommentHeight
        });
        
    }

    function loginStateChanged(_user) {
        user = _user;
        hideCommentDialog();
    }

    that = {
        // public variables
        onProgressChange: null,
        onSoundComplete: null,
        urls: urls,
        pluginTypeEnum: pluginTypeEnum,
        
        // public methods
        initialize: function(readyFunc, _updateCallback) {
            updateCallback = _updateCallback;
            compileTemplates();
            initializeJPlayer(readyFunc);
            cacheImages();
            createDialogs();

            if (Login) {
                Login.getUser(loginStateChanged);
                Login.addStateChangeCallback(loginStateChanged);
            }
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
            var song_id = parseInt($(dom).attr('data-songid'));
            if (currentSong !== null && currentSong.id === parseInt(song_id)) {
                return;
            }
            currentSong = songs[song_id];

            if (currentPlayer !== null) {
                that.seek(0);
                that.stop();
                updateCurrentPlayer();
            }

            currentPlayer = $(dom);
            currentMp3File = media_url + currentSong.mp3_file;
            jp.jPlayer('setFile', currentMp3File);
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

            song.comments_visible = true;
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
