from django.db import models
from trips.models import Itinerary
from django.db.models import JSONField  

try:
    from django.db.models import JSONField as BuiltinJSONField
    JSON_FIELD = BuiltinJSONField
except Exception:
    JSON_FIELD = JSONField

class Budget(models.Model):
    itinerary = models.OneToOneField(Itinerary, on_delete=models.CASCADE, related_name="budget")
    total_budget = models.FloatField(default=0)
    total_spent = models.FloatField(default=0)
    remaining = models.FloatField(default=0)

    # store per-category budget amounts as {"Accommodation": 1000, "Food": 500, ...}
    category_budgets = JSON_FIELD(default=dict, blank=True, null=True)

    def update_remaining(self):
        # recalc total_spent from expense records
        self.total_spent = sum(exp.amount for exp in self.expenses.all())
        # if category_budgets present, keep total_budget in sync
        if self.category_budgets:
            try:
                self.total_budget = sum(float(v) for v in self.category_budgets.values())
            except Exception:
                # if something wrong with values, ignore and keep existing total_budget
                pass
        self.remaining = self.total_budget - self.total_spent
        self.save()

    def get_category_budget(self, category_count):
        """Get per-category budget, safely handling division"""
        return self.total_budget / category_count if category_count > 0 else 0

    def __str__(self):
        try:
            return f"Budget for {self.itinerary.title}"
        except Exception:
            return f"Budget for itinerary {self.itinerary_id}"


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ("Accommodation", "Accommodation"),
        ("Transportation", "Transportation"),
        ("Food", "Food"),
        ("Activities", "Activities"),
        ("Shopping", "Shopping"),
        ("Misc", "Miscellaneous"),
    ]
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="expenses")
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="Misc")
    amount = models.FloatField()
    date = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.budget.update_remaining()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.budget.update_remaining()

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"
