from django.urls import path
from . import views

urlpatterns = [
    path("add-review/", views.add_review, name="add_review"),
]
