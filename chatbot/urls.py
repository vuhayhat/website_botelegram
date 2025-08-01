"""chatbot.urls
~~~~~~~~~~~~~~~~
URL configuration for the chatbot application.

Exposes a single endpoint at the application root (`/`) that maps to
``chatbot_view`` responsible for rendering or processing the chatbot
interface.
"""

from django.urls import path
from .views import chatbot_view

urlpatterns = [
    path('', chatbot_view, name='chatbot'),
]
