"""
Dashboard URLs

Main dashboard views based on user roles.
"""

from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import date

app_name = 'dashboard'


def home(request):
    """Main dashboard view - redirects based on role."""
    if not request.user.is_authenticated:
        return redirect('users:login')
    
    # Check user roles and redirect appropriately
    user = request.user
    roles = list(user.get_roles().values_list('name', flat=True))
    
    # Superusers should always see admin dashboard
    if user.is_superuser or 'admin' in roles:
        # Import here to avoid circular imports
        from orders.models import Order, OrderStatus
        from customers.models import CustomerProfile
        from payments.models import Payment
        
        # Get real statistics
        today = date.today()
        
        # Pending orders (not delivered)
        pending_orders = Order.objects.filter(is_deleted=False).exclude(
            current_status__status_name='delivered'
        ).count()
        
        # Completed today
        completed_today = Order.objects.filter(
            is_deleted=False,
            current_status__status_name='delivered',
            updated_at__date=today
        ).count()
        
        # Ready for delivery
        ready_for_delivery = Order.objects.filter(
            is_deleted=False,
            current_status__status_name='ready_for_delivery'
        ).count()
        
        # Monthly revenue
        month_start = today.replace(day=1)
        monthly_revenue = Payment.objects.filter(
            status='captured',
            created_at__date__gte=month_start
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        # Recent orders
        recent_orders = Order.objects.filter(is_deleted=False).select_related(
            'customer__user', 'garment_type', 'current_status'
        ).order_by('-created_at')[:5]
        
        return render(request, 'dashboard/admin_dashboard.html', {
            'user': user,
            'roles': roles,
            'pending_orders': pending_orders,
            'completed_today': completed_today,
            'ready_for_delivery': ready_for_delivery,
            'monthly_revenue': monthly_revenue,
            'recent_orders': recent_orders,
        })
    elif 'tailor' in roles:
        return render(request, 'dashboard/tailor_dashboard.html', {
            'user': user,
            'roles': roles,
        })
    elif 'delivery' in roles:
        return render(request, 'dashboard/delivery_dashboard.html', {
            'user': user,
            'roles': roles,
        })
    elif 'designer' in roles:
        return render(request, 'dashboard/designer_dashboard.html', {
            'user': user,
            'roles': roles,
        })
    elif 'customer' in roles:
        # Import here to avoid circular imports
        from orders.models import Order
        
        # Get customer profile
        customer_profile = getattr(user, 'customer_profile', None)
        
        context = {
            'user': user,
            'roles': roles,
        }
        
        if customer_profile:
            # Stats
            base_qs = Order.objects.filter(customer=customer_profile, is_deleted=False)
            
            context['total_orders'] = base_qs.count()
            context['completed_orders'] = base_qs.filter(
                current_status__status_name='delivered'
            ).count()
            context['in_progress_orders'] = base_qs.exclude(
                current_status__status_name__in=['delivered', 'cancelled']
            ).count()
            
            # Recent orders
            context['recent_orders'] = base_qs.select_related(
                'garment_type', 'current_status'
            ).order_by('-created_at')[:5]
            
        return render(request, 'dashboard/customer_dashboard.html', context)
    else:
        # Default staff dashboard
        return render(request, 'dashboard/staff_dashboard.html', {
            'user': user,
            'roles': roles,
        })


urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', home, name='dashboard'),
]
