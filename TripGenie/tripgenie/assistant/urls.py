from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chatbot_response, name='chatbot_response'),
    path('clear/', views.clear_chat, name='clear_chat'),
    path('load/', views.load_chat, name='load_chat'),
]
