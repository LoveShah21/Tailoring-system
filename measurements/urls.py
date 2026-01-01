"""URL configuration for measurements app."""
from django.urls import path
from . import views

app_name = 'measurements'

urlpatterns = [
    path('templates/', views.MeasurementTemplateListView.as_view(), name='template_list'),
    path('', views.MeasurementSetListView.as_view(), name='set_list'),
    path('create/', views.MeasurementSetCreateView.as_view(), name='set_create'),
    path('<int:pk>/', views.MeasurementSetDetailView.as_view(), name='set_detail'),
    path('<int:pk>/edit/', views.MeasurementSetEditView.as_view(), name='set_edit'),
    path('api/templates/<int:garment_type_id>/', views.TemplatesAPIView.as_view(), name='api_templates'),
]
