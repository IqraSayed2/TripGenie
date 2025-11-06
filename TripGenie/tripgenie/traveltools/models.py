# traveltools/models.py
from django.db import models
from django.contrib.auth.models import User

class ToolUsage(models.Model):
    TOOL_CHOICES = [
        ("currency", "Currency Converter"),
        ("weather", "Weather Forecast"),
        ("timezone", "World Clock"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    tool_type = models.CharField(max_length=20, choices=TOOL_CHOICES)
    query = models.CharField(max_length=200)
    result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tool_type} - {self.query[:30]}"
