"""
URL configuration for tailoring_system project.

Custom admin panel used instead of Django built-in admin.
"""

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Authentication & User Management
    path('users/', include('users.urls', namespace='users')),
    
    # Customer Portal
    path('customers/', include('customers.urls', namespace='customers')),
    
    # Catalog Management
    path('catalog/', include('catalog.urls', namespace='catalog')),
    
    # Inventory Management
    path('inventory/', include('inventory.urls', namespace='inventory')),
    
    # Measurements
    path('measurements/', include('measurements.urls', namespace='measurements')),
    
    # Designs
    path('designs/', include('designs.urls', namespace='designs')),
    
    # Orders
    path('orders/', include('orders.urls', namespace='orders')),
    
    # Trials & Alterations
    path('trials/', include('trials.urls', namespace='trials')),
    
    # Billing & Invoicing
    path('billing/', include('billing.urls', namespace='billing')),
    
    # Payments (including Razorpay webhooks)
    path('payments/', include('payments.urls', namespace='payments')),
    
    # Delivery
    path('delivery/', include('delivery.urls', namespace='delivery')),
    
    # Notifications
    path('notifications/', include('notifications.urls', namespace='notifications')),
    
    # Feedback
    path('feedback/', include('feedback.urls', namespace='feedback')),
    
    # Reporting & Analytics
    path('reporting/', include('reporting.urls', namespace='reporting')),
    
    # Audit Logs
    path('audit/', include('audit.urls', namespace='audit')),
    
    # System Configuration
    path('config/', include('config.urls', namespace='config')),
    
    # Dashboard (Home)
    path('', include('users.dashboard_urls', namespace='dashboard')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
