from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name="jst_escape")
@stringfilter
def jst_escape(code):
    """
    escape code so that it can fit inside a javascript string.

    we need to escape:
        backslashes
        single quotes
        double quotes
        newlines
        tabs
    """
    return code.replace("\\", "\\\\").replace("'", "\\'").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
