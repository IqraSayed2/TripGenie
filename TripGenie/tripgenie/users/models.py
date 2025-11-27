from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta, date

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    username_changed_at = models.DateField(null=True, blank=True)

    @property
    def username_cooldown(self):
        if not self.username_changed_at:
            return None
        days_passed = (date.today() - self.username_changed_at).days
        if days_passed < 14:
            return 14 - days_passed
        return None

    def __str__(self):
        return self.user.username
