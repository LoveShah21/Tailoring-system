"""
Users App - Services

Business logic for user management, role assignment, and authentication.
All critical operations wrapped in @transaction.atomic.
"""

from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from .models import User, Role, UserRole, Permission, RolePermission


class UserService:
    """Service class for user management operations."""
    
    @staticmethod
    @transaction.atomic
    def create_user(username, email, password, first_name='', last_name='', 
                    created_by=None, roles=None):
        """
        Create a new user with optional role assignment.
        
        Args:
            username: Unique username
            email: Unique email address
            password: Plain text password (will be hashed)
            first_name: Optional first name
            last_name: Optional last name
            created_by: User who is creating this user (for audit)
            roles: List of role names to assign
        
        Returns:
            Created User instance
        
        Raises:
            ValidationError: If username or email already exists
        """
        # Check for existing username/email
        if User.objects.all_with_deleted().filter(username=username).exists():
            raise ValidationError('Username already exists')
        if User.objects.all_with_deleted().filter(email=email).exists():
            raise ValidationError('Email already exists')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Assign roles if provided
        if roles:
            for role_name in roles:
                RoleService.assign_role(user, role_name, assigned_by=created_by)
        
        return user
    
    @staticmethod
    @transaction.atomic
    def update_user(user, **kwargs):
        """
        Update user details.
        
        Args:
            user: User instance to update
            **kwargs: Fields to update (first_name, last_name, email, etc.)
        
        Returns:
            Updated User instance
        """
        allowed_fields = ['first_name', 'last_name', 'email', 'is_active']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(user, field, value)
        
        user.save()
        return user
    
    @staticmethod
    @transaction.atomic
    def change_password(user, new_password):
        """Change user password."""
        user.set_password(new_password)
        user.save(update_fields=['password', 'updated_at'])
        return user
    
    @staticmethod
    @transaction.atomic
    def soft_delete_user(user):
        """Soft delete a user."""
        user.soft_delete()
        return user
    
    @staticmethod
    @transaction.atomic
    def restore_user(user):
        """Restore a soft-deleted user."""
        user.restore()
        return user
    
    @staticmethod
    def get_user_by_username(username):
        """Get active user by username."""
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_by_email(email):
        """Get active user by email."""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def get_users_by_role(role_name):
        """Get all active users with a specific role."""
        return User.objects.filter(
            user_roles__role__name=role_name,
            user_roles__is_deleted=False,
            is_active=True
        ).distinct()
    
    @staticmethod
    def authenticate_user(request, username, password):
        """
        Authenticate user by username/email and password.
        
        Returns:
            User instance if authenticated, None otherwise
        """
        # Try username first
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            # Try email
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        return user
    
    @staticmethod
    def login_user(request, user):
        """Log in a user."""
        login(request, user)
    
    @staticmethod
    def logout_user(request):
        """Log out the current user."""
        logout(request)


class RoleService:
    """Service class for role management operations."""
    
    @staticmethod
    @transaction.atomic
    def create_role(name, description=''):
        """Create a new role."""
        if Role.objects.filter(name=name).exists():
            raise ValidationError(f'Role "{name}" already exists')
        
        return Role.objects.create(name=name, description=description)
    
    @staticmethod
    @transaction.atomic
    def assign_role(user, role_name, assigned_by=None):
        """
        Assign a role to a user.
        
        Args:
            user: User instance
            role_name: Name of the role to assign
            assigned_by: User who is making the assignment
        
        Returns:
            UserRole instance
        """
        try:
            role = Role.objects.get(name=role_name, is_deleted=False)
        except Role.DoesNotExist:
            raise ValidationError(f'Role "{role_name}" does not exist')
        
        # Check if already assigned
        existing = UserRole.objects.filter(user=user, role=role).first()
        if existing:
            if existing.is_deleted:
                # Restore the assignment
                existing.is_deleted = False
                existing.assigned_by = assigned_by
                existing.save()
                return existing
            else:
                raise ValidationError(f'User already has role "{role_name}"')
        
        return UserRole.objects.create(
            user=user,
            role=role,
            assigned_by=assigned_by
        )
    
    @staticmethod
    @transaction.atomic
    def revoke_role(user, role_name):
        """Revoke a role from a user (soft delete)."""
        try:
            user_role = UserRole.objects.get(
                user=user,
                role__name=role_name,
                is_deleted=False
            )
            user_role.is_deleted = True
            user_role.save()
            return True
        except UserRole.DoesNotExist:
            return False
    
    @staticmethod
    def get_all_roles():
        """Get all active roles."""
        return Role.objects.filter(is_deleted=False)
    
    @staticmethod
    def get_role_users(role_name):
        """Get all users with a specific role."""
        return User.objects.filter(
            user_roles__role__name=role_name,
            user_roles__is_deleted=False
        )


class PermissionService:
    """Service class for permission management operations."""
    
    @staticmethod
    @transaction.atomic
    def create_permission(name, description=''):
        """Create a new permission."""
        if Permission.objects.filter(name=name).exists():
            raise ValidationError(f'Permission "{name}" already exists')
        
        return Permission.objects.create(name=name, description=description)
    
    @staticmethod
    @transaction.atomic
    def assign_permission_to_role(role_name, permission_name):
        """Assign a permission to a role."""
        try:
            role = Role.objects.get(name=role_name, is_deleted=False)
        except Role.DoesNotExist:
            raise ValidationError(f'Role "{role_name}" does not exist')
        
        try:
            permission = Permission.objects.get(name=permission_name)
        except Permission.DoesNotExist:
            raise ValidationError(f'Permission "{permission_name}" does not exist')
        
        role_perm, created = RolePermission.objects.get_or_create(
            role=role,
            permission=permission
        )
        return role_perm
    
    @staticmethod
    @transaction.atomic
    def revoke_permission_from_role(role_name, permission_name):
        """Revoke a permission from a role."""
        try:
            role_perm = RolePermission.objects.get(
                role__name=role_name,
                permission__name=permission_name
            )
            role_perm.delete()
            return True
        except RolePermission.DoesNotExist:
            return False
    
    @staticmethod
    def get_role_permissions(role_name):
        """Get all permissions for a role."""
        return Permission.objects.filter(
            role_permissions__role__name=role_name
        )
    
    @staticmethod
    def user_has_permission(user, permission_name):
        """Check if user has a specific permission."""
        return user.has_permission(permission_name)
