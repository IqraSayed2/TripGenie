from django.db import models
from django.contrib.auth.models import User

class MembershipPlan(models.Model):
    name = models.CharField(max_length=50)
    monthly_price = models.IntegerField(default=0) 
    yearly_price = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    features = models.JSONField(default=list)
    features_excluded = models.JSONField(default=list, blank=True)
    yearly_savings_text = models.CharField(max_length=100, blank=True)
    icon_class = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class UserMembership(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(MembershipPlan, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=False)
    valid_till = models.DateField(null=True, blank=True)
    billing_period = models.CharField(max_length=10, choices=(('monthly','Monthly'),('yearly','Yearly')), default='monthly')

    def __str__(self):
        return f"{self.user.username} - {self.plan}"
    

class MembershipPayment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(MembershipPlan, on_delete=models.SET_NULL, null=True)
    order_id = models.CharField(max_length=200)
    payment_id = models.CharField(max_length=200, null=True, blank=True)
    status = models.CharField(max_length=20, choices=(
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed')
    ), default='FAILED')
    amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Show stored amount (stored in paise) as rupees for readability
        try:
            amt = f"₹{(self.amount / 100):.2f}" if self.amount is not None else "-"
        except Exception:
            amt = "-"
        return f"{self.user} - {self.plan} - {amt} - {self.status}"

    @property
    def amount_in_rupees(self):
        """Return the stored amount (paise) as rupees (float)."""
        try:
            return (self.amount or 0) / 100.0
        except Exception:
            return None

