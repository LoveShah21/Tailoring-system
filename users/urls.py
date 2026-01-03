"""
Users App - URLs

URL patterns for user authentication and management.
"""

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views, forms

app_name = 'users'

urlpatterns = [
    # Authentication
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('profile/password/', views.PasswordChangeView.as_view(), name='password_change'),
    
    # Admin - User Management
    path('admin/users/', views.AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/create/', views.AdminUserCreateView.as_view(), name='admin_user_create'),
    path('admin/users/<int:pk>/', views.AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('admin/users/<int:pk>/edit/', views.AdminUserEditView.as_view(), name='admin_user_edit'),
    path('admin/users/<int:pk>/toggle-status/', views.AdminUserToggleStatusView.as_view(), name='admin_user_toggle_status'),
    
    # Admin - Role Management
    path('admin/roles/', views.AdminRoleListView.as_view(), name='admin_role_list'),
    path('admin/roles/create/', views.AdminRoleCreateView.as_view(), name='admin_role_create'),
    path('admin/roles/<int:pk>/edit/', views.AdminRoleEditView.as_view(), name='admin_role_edit'),
    
    # Password Reset
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='users/password_reset_form.html',
        form_class=forms.CustomPasswordResetForm,
        success_url=reverse_lazy('users:password_reset_done')
    ), name='password_reset'),
    
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
        form_class=forms.CustomSetPasswordForm,
        success_url=reverse_lazy('users:password_reset_complete')
    ), name='password_reset_confirm'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
]
