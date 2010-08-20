var SCProject = function () {
    // private variables
    var that;

    // configurable stuff
    var stateRequestTimeout = 10000;

    var template_version_list = "{% filter escapejs %}{% include 'workbench/version_list.jst.html' %}{% endfilter %}";
    var template_version_list_s = null;
    var template_footer = "{% filter escapejs %}{% include 'workbench/project_footer.jst.html' %}{% endfilter %}";
    var template_footer_s = null;
    var template_sample_upload_row = "{% filter escapejs %}{% include 'workbench/sample_upload_row.jst.html' %}{% endfilter %}";
    var template_sample_upload_row_s = null;

    var state = {
        urls: {% include 'workbench/urls.jst.html' %},
        versions: [],
        project: null,
        user: null
    };

    var last_version_id = null;
    var temp_version_count = 0;

    var band_id;
    var project_id;
    
    // private functions
    function reloadEverything() {
        last_version_id = null;
        temp_version_count = 0;
        state.versions = []
        that.ajaxRequest();
    }

    function addClicksToProjects() {
        function uploadSamplesStartCallback() {

        }

        function uploadSamplesCompleteCallback(response) {
            // sometimes the response is wrapped in <pre></pre>
            // for some strange reason
            if (response.indexOf('<pre>') === 0) {
                response = response.substr(5, response.length-'<pre>'.length-'</pre>'.length);
            }

            var result = eval('(' + response + ')');
            if (result.success === true) {
                reloadEverything();
            } else {
                alert("Unable to process upload:\n\n" + result.reason);
            }
        }

        function missing_samples_upload_f() {
            return AIM.submit(this, {
                'onStart': uploadSamplesStartCallback,
                'onComplete': uploadSamplesCompleteCallback
            });
        };

        function add_file_f() {
            $(this).closest('tr').before(Jst.evaluate(template_sample_upload_row_s, {}));
            SCTips.addUi($(this).closest('table'));
            return false;
        };

        function missing_project_upload_f() {
            return AIM.submit(this, {
                'onStart': uploadSamplesStartCallback,
                'onComplete': uploadSamplesCompleteCallback
            });
        };

        function missing_mp3_upload_f() {
            return AIM.submit(this, {
                'onStart': uploadSamplesStartCallback,
                'onComplete': uploadSamplesCompleteCallback
            });
        };

        for (var i=0; i<state.versions.length; ++i) {
            $("#missing-samples-upload-"+i).submit(missing_samples_upload_f);
            $("#add-file-"+i).click(add_file_f);

            $("#missing-project-upload-"+i).submit(missing_project_upload_f);
            $("#missing-mp3-upload-"+i).submit(missing_mp3_upload_f);
        }

        $("#checkout").click(function(){
            $.post(
                state.urls.ajax_checkout,
                {
                    project: project_id
                },
                function(data) {
                    if (data === null) {
                        alert("Unable to check out project.");
                        return;
                    }
                    if (! data.success) {
                        alert("Unable to check out project: " + data.reason);
                        return;
                    }
                    state.project.checked_out_to = state.user;
                    updateProjects();
                },
                'json');

            return false;
        });

        $("#just-check-in").click(function(){
            $.post(
                state.urls.ajax_checkin,
                {
                    project: project_id
                },
                function (data) {
                    if (data === null) {
                        alert("Unable to check in project.");
                        return;
                    }
                    if (! data.success) {
                        alert("Unable to check in project: " + data.reason);
                        return;
                    }

                    state.project.checked_out_to = null;
                    updateProjects();
                },
                'json');
            return false;
        });

        $("#checkin-form").submit(function(){
            return AIM.submit(this, {
                onStart: function(){},
                onComplete: function(response) {
                    // sometimes the response is wrapped in <pre></pre>
                    // for some strange reason
                    if (response.indexOf('<pre>') === 0) {
                        response = response.substr(5, response.length-'<pre>'.length-'</pre>'.length);
                    }

                    var data = eval('(' + response + ')');

                    if (data.success) {
                        ajaxRequestProject();
                        state.project.checked_out_to = null;
                        updateProjects();
                    } else {
                        alert("Error checking in: " + data.reason);
                    }
                }
            });
        });

        $("#upload-samples").click(function(){
            // toggle visibility
            var div = $("#action-upload-samples");
            if (div.is(':visible')) {
                div.hide();
            } else {
                div.show();
            }
            return false;
        });

        $("#action-upload-samples .add-file").click(add_file_f);

        $("#action-upload-samples-form").submit(function(){
            return AIM.submit(this, {
                onStart: function() {},
                onComplete: function(response) {
                    // sometimes the response is wrapped in <pre></pre>
                    // for some strange reason
                    if (response.indexOf('<pre>') === 0) {
                        response = response.substr(5, response.length-'<pre>'.length-'</pre>'.length);
                    }
                    
                    var data = eval('(' + response + ')');

                    if (data.success) {
                        reloadEverything();
                    } else {
                        alert("Error uploading samples: " + data.reason);
                    }
                }
            });
        });

        $("#rename").click(function(){
            // toggle visibility
            var div = $("#action-rename");
            if (div.is(':visible')) {
                div.hide();
            } else {
                div.show();
            }
            return false;
        });

        $("#action-rename-form").submit(function(){
            return AIM.submit(this, {
                onStart: function() {},
                onComplete: function(response) {
                    // sometimes the response is wrapped in <pre></pre>
                    // for some strange reason
                    if (response.indexOf('<pre>') === 0) {
                        response = response.substr(5, response.length-'<pre>'.length-'</pre>'.length);
                    }
                    
                    var data = eval('(' + response + ')');

                    if (data.success) {
                        ajaxRequestProject();
                    } else {
                        alert("Error renaming project: " + data.reason);
                    }
                }
            });
        });
    }

    function updateProjects() {
        if (state.json === null) {
            return;
        }

        $("#projects").html(Jst.evaluate(template_version_list_s, state));
        Player.addUi("#projects");
        Player.addCommentsUi("#projects");
        SCTips.addUi("#projects");
        addClicksToProjects();

        $("#footer-data").html(Jst.evaluate(template_footer_s, state));
        SCTips.addUi("#footer-data");
    }

    function ajaxRequestLoop() {
        that.ajaxRequest();
        setTimeout(ajaxRequestLoop, stateRequestTimeout);
    }

    function compileTemplates() {
        template_version_list_s = Jst.compile(template_version_list);
        template_footer_s = Jst.compile(template_footer);
        template_sample_upload_row_s = Jst.compile(template_sample_upload_row);
    }
    
    function scrollToNewestVersion() {
        // TODO
    }

    function ajaxRequestProject() {
        $.getJSON(
            state.urls.ajax_project,
            {
                last_version: last_version_id,
                project: project_id,
            },
            function(data){
                if (data === null) {
                    return;
                }

                if (! data.success) {
                    return;
                }

                state.project = data.project;
                state.user = data.user;

                // clear temporary versions
                while (temp_version_count > 0) {
                    state.versions.pop();
                    --temp_version_count;
                }

                // sort incoming versions
                var versionCount = 0;
                if (data.versions.length) {
                    versionCount = data.versions.length;
                }
                if (versionCount > 0) {
                    data.versions.sort(function(a,b){
                        return a.id - b.id;
                    });
                }

                // return the index of where a new version should be inserted.
                // -1 if the version already exists
                function getVersionIndex(id) {
                    // loop backwards through the array until we find the
                    // slot for the version
                    var i;
                    for (i=state.versions.length-1; i>=0; --i) {
                        if (state.versions[i].id < id) {
                            return i+1;
                        } else if (state.versions[i].id === id) {
                            return -1;
                        }
                    }
                    // there are no versions
                    return 0;
                }

                // insert the new versions into the sorted list
                var i;
                var insertIndex;
                var version;
                for (i=0; i<versionCount; ++i) {
                    version = data.versions[i];
                    if (version.song) {
                        Player.processSong(version.song);
                    }
                    insertIndex = getVersionIndex(version.id);
                    if (insertIndex !== -1) {
                        state.versions.splice(insertIndex, 0, version);
                    }
                }
                if (versionCount > 0) {
                    last_version_id = data.versions[versionCount-1].id;
                    updateProjects();
                    scrollToNewestVersion();
                }
            }
        );
    }

    that = {
        // public variables
        
        // public functions
        initialize: function (init_band_id, init_project_id) {
            Login.addStateChangeCallback(that.ajaxRequest);
            compileTemplates();
            band_id = init_band_id;
            project_id = init_project_id;

            Player.initialize(null, updateProjects);

            ajaxRequestLoop();
        },
        
        ajaxRequest: function () {
            ajaxRequestProject();
        }
    };
    return that;
} ();
$(document).ready(function(){
    SCProject.initialize(band_id, project_id);
});


