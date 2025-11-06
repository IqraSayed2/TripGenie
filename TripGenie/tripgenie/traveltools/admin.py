# traveltools/admin.py
from django.contrib import admin
from .models import ToolUsage

@admin.register(ToolUsage)
class ToolUsageAdmin(admin.ModelAdmin):
    list_display = ("user", "tool_type", "query", "created_at")
    list_filter = ("tool_type", "created_at")
    search_fields = ("query",)
