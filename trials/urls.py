"""URL configuration for trials app."""
from django.urls import path
from . import views

app_name = 'trials'

urlpatterns = [
    path('', views.TrialListView.as_view(), name='trial_list'),
    path('schedule/', views.TrialCreateView.as_view(), name='trial_create'),
    path('<int:pk>/', views.TrialDetailView.as_view(), name='trial_detail'),
    path('<int:pk>/update/', views.TrialUpdateView.as_view(), name='trial_update'),
    path('<int:trial_pk>/alteration/', views.AddAlterationView.as_view(), name='add_alteration'),
    path('alteration/<int:pk>/complete/', views.MarkAlterationCompleteView.as_view(), name='complete_alteration'),
]
