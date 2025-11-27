from django import template
from membership.utils import get_user_membership

register = template.Library()

@register.filter
def is_premium(user):
    membership = get_user_membership(user)
    return membership and membership.plan.monthly_price > 0
