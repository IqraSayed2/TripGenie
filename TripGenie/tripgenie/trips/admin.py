from django.contrib import admin
from .models import Trip, Wishlist, Itinerary, ItineraryDay, Activity


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
	list_display = (
		"name",
		"user",
		"country",
		"duration",
		"estimated_cost",
		"category",
		"created_at",
	)
	search_fields = ("name", "user__username", "country", "category")
	list_filter = ("country", "category", "created_at")
	prepopulated_fields = {"slug": ("name",)}
	readonly_fields = ("created_at",)
	ordering = ("-created_at",)


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
	list_display = ("title", "trip", "user", "total_days", "created_at")
	search_fields = ("title", "trip__name", "user__username")
	list_filter = ("total_days", "created_at")
	readonly_fields = ("created_at",)


@admin.register(ItineraryDay)
class ItineraryDayAdmin(admin.ModelAdmin):
	list_display = ("itinerary", "day_index", "date")
	list_filter = ("date",)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
	list_display = ("title", "itinerary_day", "cost")
	search_fields = ("title",)

