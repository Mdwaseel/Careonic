from django import template

register = template.Library()

@register.filter
def add_class(field, css_class):
    return field.as_widget(attrs={"class": f"{css_class} {'is-invalid' if field.errors else ''}"})