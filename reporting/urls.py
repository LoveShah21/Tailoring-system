"""URL configuration for reporting app."""
from django.urls import path
from . import views

app_name = 'reporting'

urlpatterns = [
    path('', views.ReportingDashboardView.as_view(), name='dashboard'),
    path('revenue/', views.RevenueReportView.as_view(), name='revenue'),
    path('orders/', views.OrdersReportView.as_view(), name='orders'),
    path('export/revenue/', views.ExportRevenueCSVView.as_view(), name='export_revenue'),
    path('export/orders/', views.ExportOrdersCSVView.as_view(), name='export_orders'),
]
