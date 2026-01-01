"""URL configuration for catalog app."""
from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    # Garment Types
    path('garments/', views.GarmentTypeListView.as_view(), name='garment_list'),
    path('garments/add/', views.GarmentTypeCreateView.as_view(), name='garment_create'),
    path('garments/<int:pk>/', views.GarmentTypeDetailView.as_view(), name='garment_detail'),
    path('garments/<int:pk>/edit/', views.GarmentTypeEditView.as_view(), name='garment_edit'),
    
    # Work Types
    path('work-types/', views.WorkTypeListView.as_view(), name='work_type_list'),
    path('work-types/add/', views.WorkTypeCreateView.as_view(), name='work_type_create'),
    path('work-types/<int:pk>/edit/', views.WorkTypeEditView.as_view(), name='work_type_edit'),
    
    # Mappings
    path('garments/<int:garment_pk>/toggle-work/<int:work_type_pk>/', 
         views.GarmentWorkTypeMappingView.as_view(), name='toggle_work_type'),
]
