"""
Users App - URLs

URL patterns for user authentication and management.
"""

from django.urls import path
from . import views

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
]
