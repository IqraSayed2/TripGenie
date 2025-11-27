from .models import UserMembership

def get_user_membership(user):
    if not user.is_authenticated:
        return None

    try:
        membership = UserMembership.objects.select_related("plan").get(user=user)
        if membership.is_active:
            return membership
        return None
    except UserMembership.DoesNotExist:
        return None
