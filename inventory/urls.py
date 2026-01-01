"""URL configuration for inventory app."""
from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Fabrics
    path('', views.FabricListView.as_view(), name='fabric_list'),
    path('add/', views.FabricCreateView.as_view(), name='fabric_create'),
    path('<int:pk>/', views.FabricDetailView.as_view(), name='fabric_detail'),
    path('<int:pk>/edit/', views.FabricEditView.as_view(), name='fabric_edit'),
    
    # Stock transactions
    path('<int:pk>/stock-in/', views.StockInView.as_view(), name='stock_in'),
    path('<int:pk>/stock-out/', views.StockOutView.as_view(), name='stock_out'),
    
    # Alerts
    path('alerts/', views.LowStockAlertListView.as_view(), name='alert_list'),
    path('alerts/<int:pk>/resolve/', views.ResolveAlertView.as_view(), name='resolve_alert'),
]
