from __future__ import annotations

from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(bound_field, css_class: str):
    """Append a CSS class to a Django BoundField widget."""
    if bound_field is None:
        return bound_field

    try:
        existing = bound_field.field.widget.attrs.get("class", "")
    except Exception:
        existing = ""

    css_class = (css_class or "").strip()
    if not css_class:
        return bound_field

    if existing:
        new_class = f"{existing} {css_class}".strip()
    else:
        new_class = css_class

    return bound_field.as_widget(attrs={"class": new_class})
