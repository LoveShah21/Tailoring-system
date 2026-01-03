"""URL configuration for orders app."""
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Order CRUD
    path('', views.OrderListView.as_view(), name='order_list'),
    path('create/', views.OrderCreateView.as_view(), name='order_create'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('<int:pk>/edit/', views.OrderEditView.as_view(), name='order_edit'),
    path('<int:pk>/delete/', views.OrderDeleteView.as_view(), name='order_delete'),
    
    # Customer View
    path('my-orders/<int:pk>/', views.CustomerOrderDetailView.as_view(), name='customer_order_detail'),
    
    # Order actions
    path('<int:pk>/transition/', views.OrderTransitionView.as_view(), name='order_transition'),
    path('<int:pk>/assign/', views.OrderAssignView.as_view(), name='order_assign'),
    path('<int:pk>/allocate/', views.OrderAllocateMaterialView.as_view(), name='order_allocate'),
    
    # AJAX APIs
    path('api/measurements/<int:customer_id>/', views.OrderMeasurementsAPI.as_view(), name='api_measurements'),
    path('api/work-types/<int:garment_type_id>/', views.OrderWorkTypesAPI.as_view(), name='api_work_types'),
]
