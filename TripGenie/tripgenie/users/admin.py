from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# Register your models here.

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_phone', 'is_staff', 'get_email_verified')

    def get_phone(self, obj):
        return obj.userprofile.phone if hasattr(obj, 'userprofile') else '-'
    get_phone.short_description = 'Phone'

    def get_email_verified(self, obj):
        return obj.userprofile.email_verified if hasattr(obj, 'userprofile') else False
    get_email_verified.boolean = True
    get_email_verified.short_description = 'Email verified'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


admin.site.site_header = "TripGenie"
