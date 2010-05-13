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
        "{% filter escapejs %}{% url arena.ajax_unvote 0 %}{% endfilter %}".replace(0, id);
    },
    ajax_submit_entry: "{% filter escapejs %}{% url arena.ajax_submit_entry %}{% endfilter %}",
    create: "{% filter escapejs %}{% url arena.create %}{% endfilter %}",
    compete: function (id) {
        return "{% filter escapejs %}{% url arena.compete 0 %}{% endfilter %}".replace(0, id);
    }
}
