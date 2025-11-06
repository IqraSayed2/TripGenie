# traveltools/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.tools, name="tools"),
    path("api/convert-currency/", views.convert_currency, name="convert_currency"),
    path("api/get-weather/", views.get_weather, name="get_weather"),
    path("api/get-timezone/", views.get_timezone, name="get_timezone"),
]
