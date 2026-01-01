"""
Dashboard URLs

Main dashboard views based on user roles.
"""

from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

app_name = 'dashboard'


def home(request):
    """Main dashboard view - redirects based on role."""
    if not request.user.is_authenticated:
        return redirect('users:login')
    
    # Check user roles and redirect appropriately
    user = request.user
    roles = user.get_roles().values_list('name', flat=True)
    
    if 'admin' in roles:
        return render(request, 'dashboard/admin_dashboard.html', {
            'user': user,
            'roles': roles,
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
        return render(request, 'dashboard/customer_dashboard.html', {
            'user': user,
            'roles': roles,
        })
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
