# subscriptions/models.py
from django.conf import settings
from django.db import models
from account.models import User

class StripeCustomer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.stripe_customer_id}"

class Subscription(models.Model):
    PLAN_CHOICES = (('basic','basic'),('pro','pro'),('elite','elite'))
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="subscriptions")
    stripe_subscription_id = models.CharField(max_length=255, unique=True)
    stripe_price_id = models.CharField(max_length=255)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    status = models.CharField(max_length=50)  # active, past_due, canceled, etc.
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
