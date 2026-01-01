"""URL configuration for designs app."""
from django.urls import path
from . import views

app_name = 'designs'

urlpatterns = [
    path('', views.DesignListView.as_view(), name='design_list'),
    path('<int:pk>/', views.DesignDetailView.as_view(), name='design_detail'),
    path('upload/', views.DesignCreateView.as_view(), name='design_create'),
    path('<int:pk>/status/', views.DesignStatusUpdateView.as_view(), name='update_status'),
    path('<int:design_pk>/note/', views.AddCustomizationNoteView.as_view(), name='add_note'),
]
