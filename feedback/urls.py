"""URL configuration for feedback app."""
from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('', views.FeedbackListView.as_view(), name='feedback_list'),
    path('<int:pk>/', views.FeedbackDetailView.as_view(), name='feedback_detail'),
    path('submit/', views.FeedbackCreateView.as_view(), name='feedback_create'),
    path('<int:pk>/approve/', views.ApproveFeedbackView.as_view(), name='approve'),
    path('<int:pk>/reject/', views.RejectFeedbackView.as_view(), name='reject'),
]
