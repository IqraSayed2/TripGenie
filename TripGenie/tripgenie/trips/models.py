from django.db import models
from django.contrib.auth.models import User


class Trip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trips")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, default='')
    country = models.CharField(max_length=100, blank=True, null=True)
    duration = models.PositiveIntegerField(default=3)
    estimated_cost = models.FloatField(default=0)
    category = models.CharField(max_length=100, blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    inclusions = models.JSONField(default=list, blank=True, null=True)
    exclusions = models.JSONField(default=list, blank=True, null=True)
    highlights = models.JSONField(default=list, blank=True, null=True)
    best_time = models.CharField(max_length=200, blank=True, null=True)
    rating = models.FloatField(default=4.5)
    match_score = models.IntegerField(default=80)
    travel_tips = models.TextField(blank=True, null=True)
    hotels = models.JSONField(default=list, blank=True, null=True)
    restaurants = models.JSONField(default=list, blank=True, null=True)
    local_transport = models.JSONField(default=list, blank=True, null=True)
    cost_breakdown = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"
        
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            # Create initial slug
            slug = slugify(self.name)
            # Check if slug exists
            exists = type(self).objects.filter(slug=slug).exists()
            counter = 1
            original_slug = slug
            # If slug exists, append counter until unique
            while exists:
                slug = f"{original_slug}-{counter}"
                counter += 1
                exists = type(self).objects.filter(slug=slug).exists()
            self.slug = slug
        super().save(*args, **kwargs)


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    destination_name = models.CharField(max_length=200)
    country = models.CharField(max_length=100, blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    estimated_cost = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.destination_name} ({self.user.username})"


class Itinerary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="itineraries")
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="itinerary_trip")
    title = models.CharField(max_length=200)
    total_days = models.PositiveIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Itinerary for {self.trip.name}"


class ItineraryDay(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name="days")
    day_index = models.PositiveIntegerField()
    date = models.DateField(blank=True, null=True)

    class Meta:
        unique_together = ("itinerary", "day_index")

    def __str__(self):
        return f"Day {self.day_index} - {self.itinerary.trip.name}"


class Activity(models.Model):
    itinerary_day = models.ForeignKey(ItineraryDay, on_delete=models.CASCADE, related_name="activities")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    cost = models.FloatField(default=0)

    def __str__(self):
        return f"{self.title} ({self.itinerary_day})"
