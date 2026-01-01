"""URL configuration for delivery app."""
from django.urls import path
from . import views

app_name = 'delivery'

urlpatterns = [
    path('', views.DeliveryListView.as_view(), name='delivery_list'),
    path('schedule/', views.DeliveryCreateView.as_view(), name='delivery_create'),
    path('<int:pk>/', views.DeliveryDetailView.as_view(), name='delivery_detail'),
    path('<int:pk>/update/', views.DeliveryUpdateView.as_view(), name='delivery_update'),
    path('zones/', views.DeliveryZoneListView.as_view(), name='zone_list'),
]
