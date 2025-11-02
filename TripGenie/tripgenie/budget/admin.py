from django.contrib import admin
from .models import Budget, Expense


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
	list_display = ("itinerary", "total_budget", "total_spent", "remaining")
	search_fields = ("itinerary__title", "itinerary__trip__name")
	readonly_fields = ("total_spent", "remaining")
	list_filter = ("total_budget",)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
	list_display = ("title", "budget", "category", "amount", "date")
	list_filter = ("category", "date")
	search_fields = ("title",)

