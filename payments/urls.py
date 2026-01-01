"""URL configuration for payments app."""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.PaymentListView.as_view(), name='payment_list'),
    path('<int:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('create/<int:bill_pk>/', views.CreatePaymentOrderView.as_view(), name='create_order'),
    path('verify/', views.VerifyPaymentView.as_view(), name='verify'),
    path('cash/<int:bill_pk>/', views.RecordCashPaymentView.as_view(), name='record_cash'),
    path('webhook/', views.RazorpayWebhookView.as_view(), name='webhook'),
]
