"""
Notifications App - URLs
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('api/list/', views.NotificationListAPI.as_view(), name='api_list'),
    path('api/mark-read/<int:pk>/', views.MarkNotificationReadAPI.as_view(), name='api_mark_read'),
    path('api/mark-all-read/', views.MarkAllReadAPI.as_view(), name='api_mark_all_read'),
]
