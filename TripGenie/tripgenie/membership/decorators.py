from django.shortcuts import redirect
from django.contrib import messages
from .utils import get_user_membership

def premium_required(view_func):
    def wrapper(request, *args, **kwargs):
        membership = get_user_membership(request.user)

        # Free users - monthly_price == 0 or membership doesn't exist
        if membership is None or membership.plan.monthly_price == 0:
            messages.error(request, "This feature is available for premium users only.")
            return redirect("membership")

        return view_func(request, *args, **kwargs)
    return wrapper
