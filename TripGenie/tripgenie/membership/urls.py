from django.urls import path
from . import views

urlpatterns = [
    path("", views.membership_page, name="membership"),
    path("create-order/<int:plan_id>/", views.create_order, name="create_order"),
    path("payment-status/", views.payment_status, name="payment_status"),
    path("payment-success/", views.payment_success, name="payment_success"),
]
 