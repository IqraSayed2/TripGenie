from django.db import models
from django.contrib.auth.models import User

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)        
    location = models.CharField(max_length=100, blank=True, null=True)
    rating = models.IntegerField(default=5)       
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def initials(self):
        parts = self.name.split()
        return "".join(p[0] for p in parts)[:2].upper()

    def __str__(self):
        return f"{self.name} — {self.rating}⭐"
