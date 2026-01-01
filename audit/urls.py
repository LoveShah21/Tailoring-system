"""URL configuration for audit app."""
from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('', views.ActivityLogListView.as_view(), name='activity_list'),
    path('payments/', views.PaymentAuditListView.as_view(), name='payment_audit_list'),
]
