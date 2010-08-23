{
    home: "{% filter escapejs %}{% url arena.home %}{% endfilter %}",
    available: "{% filter escapejs %}{% url arena.ajax_available %}{% endfilter %}",
    owned: "{% filter escapejs %}{% url arena.ajax_owned %}{% endfilter %}",
    ajax_bookmark: function (id) {
        return "{% filter escapejs %}{% url arena.ajax_bookmark 0 %}{% endfilter %}".replace(0, id);
    },
    ajax_unbookmark: function (id) {
        return "{% filter escapejs %}{% url arena.ajax_unbookmark 0 %}{% endfilter %}".replace(0, id);
    },
    ajax_compo: function (id) {
        return "{% filter escapejs %}{% url arena.ajax_compo 0 %}{% endfilter %}".replace(0, id);
    },
    ajax_vote: function (id) {
        return "{% filter escapejs %}{% url arena.ajax_vote 0 %}{% endfilter %}".replace(0, id);
    },
    ajax_unvote: function (id) {
        return "{% filter escapejs %}{% url arena.ajax_unvote 0 %}{% endfilter %}".replace(0, id);
    },
    ajax_submit_entry: "{% filter escapejs %}{% url arena.ajax_submit_entry %}{% endfilter %}",
    create: "{% filter escapejs %}{% url arena.create %}{% endfilter %}",
    compete: function (id) {
        return "{% filter escapejs %}{% url arena.compete 0 %}{% endfilter %}".replace(0, id);
    },
    project: function(band_id, project_id) {
        return "{% filter escapejs %}{% url workbench.project 0 1 %}{% endfilter %}".replace("0",
            "[~~band_id~~]").replace("1", project_id).replace("[~~band_id~~]", band_id);
    },
    project_version: function(band_id, project_id, version_number) {
        return this.project(band_id, project_id) + "#version" + version_number;
    },
    userpage: function (username) {
        return "{% filter escapejs %}{% url userpage '[~~~~]' %}{% endfilter %}".replace("[~~~~]", username);
    }
}
