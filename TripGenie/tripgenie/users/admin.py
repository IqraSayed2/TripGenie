from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# Register your models here.

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_phone', 'is_staff')

    def get_phone(self, obj):
        return obj.userprofile.phone if hasattr(obj, 'userprofile') else '-'
    get_phone.short_description = 'Phone'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


admin.site.site_header = "TripGenie"
