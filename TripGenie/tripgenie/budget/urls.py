from django.urls import path
from . import views

urlpatterns = [
    path("budget/", views.budget_page, name="budget"),
    path("budget/api/add-expense/", views.api_add_expense, name="api_add_expense"),
    path("api/recent_expenses/<int:trip_id>/", views.api_get_recent_expenses, name="api_get_recent_expenses"),
    path("budget/api/update-category/", views.api_update_category_budget, name="api_update_category_budget"),
    path('export-pdf/<int:budget_id>/', views.export_budget_pdf, name='export_budget_pdf'),
]
