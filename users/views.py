"""
Users App - Views

Views for authentication, user management, and admin panel.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q

from .models import User, Role, UserRole, Permission, RolePermission
from .forms import (
    UserLoginForm, UserRegistrationForm, UserProfileForm,
    CustomPasswordChangeForm, UserCreateForm, UserEditForm, RoleForm
)
from .services import UserService, RoleService, PermissionService
from .permissions import AdminRequiredMixin, StaffRequiredMixin, role_required


# =============================================================================
# AUTHENTICATION VIEWS
# =============================================================================

class LoginView(View):
    """User login view."""
    template_name = 'users/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        form = UserLoginForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Handle remember me
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
            
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            
            # Redirect based on role
            next_url = request.GET.get('next', '')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard:home')
        
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """User logout view."""
    
    def get(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('users:login')
    
    def post(self, request):
        return self.get(request)


class RegisterView(View):
    """User registration view (for customers)."""
    template_name = 'users/register.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        form = UserRegistrationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Assign customer role by default
            try:
                RoleService.assign_role(user, 'customer')
            except Exception:
                pass  # Role might not exist yet
            
            messages.success(request, 'Registration successful! Please login.')
            return redirect('users:login')
        
        return render(request, self.template_name, {'form': form})


# =============================================================================
# PROFILE VIEWS
# =============================================================================

@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    """User profile view."""
    template_name = 'users/profile.html'
    
    def get(self, request):
        return render(request, self.template_name, {
            'user': request.user,
            'roles': request.user.get_roles(),
        })


@method_decorator(login_required, name='dispatch')
class ProfileEditView(View):
    """Edit user profile view."""
    template_name = 'users/profile_edit.html'
    
    def get(self, request):
        form = UserProfileForm(instance=request.user)
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
        return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class PasswordChangeView(View):
    """Change password view."""
    template_name = 'users/password_change.html'
    
    def get(self, request):
        form = CustomPasswordChangeForm(request.user)
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('users:profile')
        return render(request, self.template_name, {'form': form})


# =============================================================================
# ADMIN PANEL - USER MANAGEMENT
# =============================================================================

@method_decorator(login_required, name='dispatch')
class AdminUserListView(AdminRequiredMixin, ListView):
    """Admin view to list all users."""
    model = User
    template_name = 'users/admin/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-created_at')
        
        # Search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Filter by role
        role = self.request.GET.get('role', '')
        if role:
            queryset = queryset.filter(user_roles__role__name=role, user_roles__is_deleted=False)
        
        # Filter by status
        status = self.request.GET.get('status', '')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = Role.objects.filter(is_deleted=False)
        context['search'] = self.request.GET.get('search', '')
        context['selected_role'] = self.request.GET.get('role', '')
        context['selected_status'] = self.request.GET.get('status', '')
        return context


@method_decorator(login_required, name='dispatch')
class AdminUserCreateView(AdminRequiredMixin, View):
    """Admin view to create a new user."""
    template_name = 'users/admin/user_form.html'
    
    def get(self, request):
        form = UserCreateForm()
        return render(request, self.template_name, {
            'form': form,
            'title': 'Create User',
        })
    
    def post(self, request):
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Assign selected roles
            for role in form.cleaned_data.get('roles', []):
                RoleService.assign_role(user, role.name, assigned_by=request.user)
            
            messages.success(request, f'User "{user.username}" created successfully!')
            return redirect('users:admin_user_list')
        
        return render(request, self.template_name, {
            'form': form,
            'title': 'Create User',
        })


@method_decorator(login_required, name='dispatch')
class AdminUserEditView(AdminRequiredMixin, View):
    """Admin view to edit a user."""
    template_name = 'users/admin/user_form.html'
    
    def get(self, request, pk):
        user = get_object_or_404(User.objects.all_with_deleted(), pk=pk)
        form = UserEditForm(instance=user)
        form.fields['roles'].initial = user.get_roles()
        return render(request, self.template_name, {
            'form': form,
            'edit_user': user,
            'title': f'Edit User: {user.username}',
        })
    
    def post(self, request, pk):
        user = get_object_or_404(User.objects.all_with_deleted(), pk=pk)
        form = UserEditForm(request.POST, instance=user)
        
        if form.is_valid():
            user = form.save()
            
            # Update roles
            current_roles = set(user.get_roles().values_list('name', flat=True))
            new_roles = set(form.cleaned_data.get('roles', []).values_list('name', flat=True))
            
            # Revoke removed roles
            for role_name in current_roles - new_roles:
                RoleService.revoke_role(user, role_name)
            
            # Assign new roles
            for role_name in new_roles - current_roles:
                RoleService.assign_role(user, role_name, assigned_by=request.user)
            
            messages.success(request, f'User "{user.username}" updated successfully!')
            return redirect('users:admin_user_list')
        
        return render(request, self.template_name, {
            'form': form,
            'edit_user': user,
            'title': f'Edit User: {user.username}',
        })


@method_decorator(login_required, name='dispatch')
class AdminUserDetailView(AdminRequiredMixin, DetailView):
    """Admin view to see user details."""
    model = User
    template_name = 'users/admin/user_detail.html'
    context_object_name = 'view_user'
    
    def get_queryset(self):
        return User.objects.all_with_deleted()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['roles'] = user.get_roles()
        context['permissions'] = user.get_permissions()
        return context


@method_decorator(login_required, name='dispatch')
class AdminUserToggleStatusView(AdminRequiredMixin, View):
    """Admin view to toggle user active status."""
    
    def post(self, request, pk):
        user = get_object_or_404(User.objects.all_with_deleted(), pk=pk)
        
        if user == request.user:
            messages.error(request, 'You cannot deactivate your own account.')
            return redirect('users:admin_user_list')
        
        user.is_active = not user.is_active
        user.save()
        
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User "{user.username}" has been {status}.')
        return redirect('users:admin_user_list')


# =============================================================================
# ADMIN PANEL - ROLE MANAGEMENT
# =============================================================================

@method_decorator(login_required, name='dispatch')
class AdminRoleListView(AdminRequiredMixin, ListView):
    """Admin view to list all roles."""
    model = Role
    template_name = 'users/admin/role_list.html'
    context_object_name = 'roles'
    
    def get_queryset(self):
        return Role.objects.filter(is_deleted=False).order_by('name')


@method_decorator(login_required, name='dispatch')
class AdminRoleCreateView(AdminRequiredMixin, View):
    """Admin view to create a new role."""
    template_name = 'users/admin/role_form.html'
    
    def get(self, request):
        form = RoleForm()
        permissions = Permission.objects.all()
        return render(request, self.template_name, {
            'form': form,
            'permissions': permissions,
            'title': 'Create Role',
        })
    
    def post(self, request):
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            
            # Assign selected permissions
            permission_ids = request.POST.getlist('permissions')
            for perm_id in permission_ids:
                try:
                    permission = Permission.objects.get(pk=perm_id)
                    RolePermission.objects.create(role=role, permission=permission)
                except Permission.DoesNotExist:
                    pass
            
            messages.success(request, f'Role "{role.name}" created successfully!')
            return redirect('users:admin_role_list')
        
        permissions = Permission.objects.all()
        return render(request, self.template_name, {
            'form': form,
            'permissions': permissions,
            'title': 'Create Role',
        })


@method_decorator(login_required, name='dispatch')
class AdminRoleEditView(AdminRequiredMixin, View):
    """Admin view to edit a role."""
    template_name = 'users/admin/role_form.html'
    
    def get(self, request, pk):
        role = get_object_or_404(Role, pk=pk, is_deleted=False)
        form = RoleForm(instance=role)
        permissions = Permission.objects.all()
        role_permissions = role.role_permissions.values_list('permission_id', flat=True)
        
        return render(request, self.template_name, {
            'form': form,
            'role': role,
            'permissions': permissions,
            'role_permissions': list(role_permissions),
            'title': f'Edit Role: {role.name}',
        })
    
    def post(self, request, pk):
        role = get_object_or_404(Role, pk=pk, is_deleted=False)
        form = RoleForm(request.POST, instance=role)
        
        if form.is_valid():
            role = form.save()
            
            # Update permissions
            role.role_permissions.all().delete()
            permission_ids = request.POST.getlist('permissions')
            for perm_id in permission_ids:
                try:
                    permission = Permission.objects.get(pk=perm_id)
                    RolePermission.objects.create(role=role, permission=permission)
                except Permission.DoesNotExist:
                    pass
            
            messages.success(request, f'Role "{role.name}" updated successfully!')
            return redirect('users:admin_role_list')
        
        permissions = Permission.objects.all()
        return render(request, self.template_name, {
            'form': form,
            'role': role,
            'permissions': permissions,
            'title': f'Edit Role: {role.name}',
        })
