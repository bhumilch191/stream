# yourapp/templatetags/custom_filters.py
import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def linkify(text):
    url_pattern = re.compile(
        r'(https?://[^\s]+)'
    )
    result = url_pattern.sub(
        r'<a href="\1" target="_blank" rel="noopener" style="color:#3ea6ff;text-decoration:none;">\1</a>',
        text
    )
    return mark_safe(result)