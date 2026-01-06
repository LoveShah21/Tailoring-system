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
            current_status__status_name='ready'
        ).count()
        
        # Monthly revenue - use datetime to avoid timezone issues with __date
        from datetime import datetime
        month_start_dt = datetime(today.year, today.month, 1)
        monthly_revenue = Payment.objects.filter(
            status='COMPLETED',
            created_at__gte=month_start_dt
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
        from orders.models import OrderAssignment
        
        assignments = OrderAssignment.objects.filter(
            staff=user, 
            role_type='tailor'
        ).select_related(
            'order__customer__user', 
            'order__garment_type', 
            'order__current_status'
        ).order_by('-assigned_at')
        
        context = {
            'user': user,
            'roles': roles,
            'total_assigned': assignments.count(),
            'active_tasks': assignments.exclude(
                order__current_status__status_name__in=['ready', 'delivered', 'closed']
            ).count(),
            'completed_tasks': assignments.filter(
                order__current_status__status_name__in=['ready', 'delivered', 'closed']
            ).count(),
            'recent_assignments': assignments[:10]
        }
        return render(request, 'dashboard/tailor_dashboard.html', context)
    elif 'delivery' in roles:
        from orders.models import OrderAssignment
        
        assignments = OrderAssignment.objects.filter(
            staff=user, 
            role_type='delivery'
        ).select_related(
            'order__customer__user', 
            'order__garment_type', 
            'order__current_status'
        ).order_by('-assigned_at')
        
        context = {
            'user': user,
            'roles': roles,
            'total_assigned': assignments.count(),
            'pending_delivery': assignments.filter(
                order__current_status__status_name='ready'
            ).count(),
            'delivered_orders': assignments.filter(
                order__current_status__status_name='delivered'
            ).count(),
            'recent_assignments': assignments[:10]
        }
        return render(request, 'dashboard/delivery_dashboard.html', context)
    elif 'designer' in roles:
        from orders.models import OrderAssignment
        
        assignments = OrderAssignment.objects.filter(
            staff=user, 
            role_type='designer'
        ).select_related(
            'order__customer__user', 
            'order__garment_type', 
            'order__current_status'
        ).order_by('-assigned_at')
        
        context = {
            'user': user,
            'roles': roles,
            'total_assigned': assignments.count(),
            'pending_tasks': assignments.filter(
                order__current_status__status_name='booked'
            ).count(),
            'completed_tasks': assignments.exclude(
                order__current_status__status_name='booked'
            ).count(),
            'recent_assignments': assignments[:10]
        }
        return render(request, 'dashboard/designer_dashboard.html', context)
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
                'garment_type', 'current_status', 'bill__invoice'
            ).order_by('-created_at')[:5]
            
        return render(request, 'dashboard/customer_dashboard.html', context)
    else:
        # Default staff dashboard
        # Import here to avoid circular imports
        from orders.models import Order
        from customers.models import CustomerProfile
        
        today = date.today()
        
        # Stats
        pending_orders = Order.objects.filter(is_deleted=False).exclude(
            current_status__status_name__in=['delivered', 'closed']
        ).count()
        
        completed_today = Order.objects.filter(
            is_deleted=False,
            current_status__status_name='delivered',
            updated_at__date=today
        ).count()
        
        ready_for_delivery = Order.objects.filter(
            is_deleted=False,
            current_status__status_name='ready'
        ).count()
        
        total_customers = CustomerProfile.objects.filter(is_deleted=False).count()
        
        # Recent orders
        recent_orders = Order.objects.filter(is_deleted=False).select_related(
            'customer__user', 'garment_type', 'current_status'
        ).order_by('-created_at')[:5]
        
        return render(request, 'dashboard/staff_dashboard.html', {
            'user': user,
            'roles': roles,
            'pending_orders': pending_orders,
            'completed_today': completed_today,
            'ready_for_delivery': ready_for_delivery,
            'total_customers': total_customers,
            'recent_orders': recent_orders,
        })


urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', home, name='dashboard'),
]
