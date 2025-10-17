from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('profile/', views.view_profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]
