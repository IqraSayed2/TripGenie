from django.contrib import admin
from .models import MembershipPlan, UserMembership, MembershipPayment

@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "monthly_price", "yearly_price")
    search_fields = ("name",)
    list_filter = ("name",)
    ordering = ("monthly_price",)

    fieldsets = (
        ("Plan Details", {
            "fields": ("name", "description", "icon_class"),
            "description": "Example icons: fa-solid fa-star, fa-solid fa-crown"
        }), 
        ("Pricing", {
            "fields": ("monthly_price", "yearly_price", "yearly_savings_text")
        }),
        ("Features (JSON List)", {
            "fields": ("features",),
            "description": "Enter features as a JSON list, example:<br>[\"Unlimited trips\", \"PDF export\", \"Chatbot access\"]"
        }),
        ("Excluded Features (❌)", {
            "fields": ("features_excluded",),
            "description": "Optional - Example: [\"Chatbot access\", \"Priority support\"]"
        }),
    )


@admin.register(UserMembership)
class UserMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "is_active", "valid_till")
    search_fields = ("user__username", "plan__name")
    list_filter = ("is_active", "plan")
    ordering = ("-valid_till",)

    fieldsets = (
        ("User", {
            "fields": ("user",),
        }),
        ("Membership Plan", {
            "fields": ("plan", "is_active", "valid_till")
        }),
    )


@admin.register(MembershipPayment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "amount_display", "status", "created_at")
    search_fields = ("user__username", "order_id", "payment_id")
    def amount_display(self, obj):
        try:
            return f"₹{int(obj.amount or 0)}"
        except Exception:
            return "-"
    amount_display.short_description = "Amount"