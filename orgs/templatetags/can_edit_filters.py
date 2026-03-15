# orgs/templatetags/can_edit_filters.py
from django import template

register = template.Library()

@register.filter
def can_edit(obj, user):
    """Call the model's can_edit method with user"""
    return obj.can_edit(user)