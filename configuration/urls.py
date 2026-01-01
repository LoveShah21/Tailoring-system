"""URL configuration for configuration app."""
from django.urls import path
from . import views

app_name = 'configuration'

urlpatterns = [
    path('', views.SystemConfigListView.as_view(), name='config_list'),
    path('<int:pk>/edit/', views.SystemConfigUpdateView.as_view(), name='config_edit'),
    path('pricing/', views.PricingRuleListView.as_view(), name='pricing_list'),
    path('pricing/add/', views.PricingRuleCreateView.as_view(), name='pricing_create'),
    path('pricing/<int:pk>/edit/', views.PricingRuleUpdateView.as_view(), name='pricing_edit'),
]
