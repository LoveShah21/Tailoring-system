"""
Users App - Permissions

RBAC decorators and mixins for view-level permission checks.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin


def role_required(*role_names):
    """
    Decorator to check if user has any of the specified roles.
    
    Usage:
        @role_required('admin', 'staff')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please login to access this page.')
                return redirect('users:login')
            
            # Check if user has any of the required roles
            user_roles = request.user.get_roles().values_list('name', flat=True)
            if any(role in user_roles for role in role_names):
                return view_func(request, *args, **kwargs)
            
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard:home')
        
        return wrapped_view
    return decorator


def permission_required(*permission_names):
    """
    Decorator to check if user has any of the specified permissions.
    
    Usage:
        @permission_required('view_orders', 'manage_orders')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please login to access this page.')
                return redirect('users:login')
            
            # Check if user has any of the required permissions
            for perm in permission_names:
                if request.user.has_permission(perm):
                    return view_func(request, *args, **kwargs)
            
            messages.error(request, 'You do not have permission to perform this action.')
            return redirect('dashboard:home')
        
        return wrapped_view
    return decorator


def admin_required(view_func):
    """Decorator to require admin role."""
    return role_required('admin')(view_func)


def staff_required(view_func):
    """Decorator to require staff or admin role."""
    return role_required('admin', 'staff')(view_func)


class RoleRequiredMixin:
    """
    Mixin to check if user has required roles.
    
    Usage:
        class MyView(RoleRequiredMixin, View):
            required_roles = ['admin', 'staff']
    """
    required_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access this page.')
            return redirect('users:login')
        
        if self.required_roles:
            user_roles = request.user.get_roles().values_list('name', flat=True)
            if not any(role in user_roles for role in self.required_roles):
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard:home')
        
        return super().dispatch(request, *args, **kwargs)


class PermissionRequiredMixin:
    """
    Mixin to check if user has required permissions.
    
    Usage:
        class MyView(PermissionRequiredMixin, View):
            required_permissions = ['view_orders']
    """
    required_permissions = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access this page.')
            return redirect('users:login')
        
        if self.required_permissions:
            has_permission = any(
                request.user.has_permission(perm) 
                for perm in self.required_permissions
            )
            if not has_permission:
                messages.error(request, 'You do not have permission to perform this action.')
                return redirect('dashboard:home')
        
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin that requires admin role."""
    required_roles = ['admin']


class StaffRequiredMixin(RoleRequiredMixin):
    """Mixin that requires admin, staff, or assigned worker roles."""
    required_roles = ['admin', 'staff', 'tailor', 'designer', 'delivery']


class TailorRequiredMixin(RoleRequiredMixin):
    """Mixin that requires tailor, admin, or staff role."""
    required_roles = ['admin', 'staff', 'tailor']


class CustomerRequiredMixin(RoleRequiredMixin):
    """Mixin that requires customer role."""
    required_roles = ['customer', 'admin']


def check_object_permission(user, obj, permission_type='view'):
    """
    Check if user has permission to access a specific object.
    
    Args:
        user: User instance
        obj: Model instance to check permission for
        permission_type: 'view', 'edit', 'delete'
    
    Returns:
        True if user has permission, False otherwise
    """
    # Admin has all permissions
    if user.has_role('admin'):
        return True
    
    # Check object-specific permissions
    model_name = obj.__class__.__name__.lower()
    permission_name = f'{permission_type}_{model_name}'
    
    return user.has_permission(permission_name)
