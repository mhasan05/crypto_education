from django.urls import path
from . import views
from . import webhook

app_name = "subscriptions"

urlpatterns = [
    # Checkout flow
    path("create_checkout_session/", views.CreateCheckoutSessionView.as_view(), name="create_checkout_session"),
    path("checkout_success/", views.checkout_success, name="checkout_success"),
    path("checkout_cancel/", views.checkout_cancel, name="checkout_cancel"),

    # Stripe webhook endpoint
    path("webhook/stripe/", webhook.stripe_webhook, name="stripe_webhook"),
]
