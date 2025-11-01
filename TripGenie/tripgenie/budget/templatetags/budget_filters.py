from django import template

register = template.Library()

@register.filter
def div(value, arg):
    try:
        # return percentage (0-100) to make template usage consistent
        return (float(value) / float(arg) * 100) if float(arg) != 0 else 0
    except (ValueError, TypeError):
        return 0