# trips/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Reccommendation
    path('recommendations/', views.recommendations, name='recommendations'),
    path('api/generate-recommendations/', views.generate_recommendations, name='generate_recommendations'),
    path('trip/<slug:trip_slug>/', views.trip_details, name='trip_details'),

    # Itinerary
    path("itinerary/", views.itinerary_page, name="itinerary"),
    path("trips/api/save-trip/", views.save_trip_to_itinerary, name="save_trip_to_itinerary"),
    path("trips/delete/<int:trip_id>/", views.delete_trip, name="delete_trip"),
    path("trips/export/<int:trip_id>/", views.export_trip_pdf, name="export_trip_pdf"),

]