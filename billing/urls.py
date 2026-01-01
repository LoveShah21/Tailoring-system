"""URL configuration for billing app."""
from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.BillListView.as_view(), name='bill_list'),
    path('<int:pk>/', views.BillDetailView.as_view(), name='bill_detail'),
    path('generate/<int:order_pk>/', views.GenerateBillView.as_view(), name='generate_bill'),
    path('<int:bill_pk>/invoice/', views.GenerateInvoiceView.as_view(), name='generate_invoice'),
    path('invoice/<int:pk>/pdf/', views.DownloadInvoicePDFView.as_view(), name='download_pdf'),
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
]
