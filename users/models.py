"""
Users App - Models

Custom User model extending AbstractUser for:
- Full Django auth compatibility
- Soft delete support
- Role-based access control

Maps to tables: users_user, users_role, users_user_role, 
                users_permission, users_role_permission
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for User model."""
    
    def create_user(self, username, email, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)
    
    def get_queryset(self):
        """Override to exclude soft-deleted users by default."""
        return super().get_queryset().filter(is_deleted=False)
    
    def all_with_deleted(self):
        """Return all users including soft-deleted."""
        return super().get_queryset()


class User(AbstractUser):
    """
    Custom User model extending AbstractUser.
    
    Maps to: users_user table
    
    Uses AbstractUser (SAFER approach) for:
    - Full Django admin compatibility
    - Built-in authentication machinery
    - Less migration risk
    """
    
    # Override email to make it required and unique
    email = models.EmailField(
        'email address',
        max_length=254,
        unique=True,
        error_messages={
            'unique': 'A user with that email already exists.',
        },
    )
    
    # Soft delete flag
    is_deleted = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    class Meta:
        db_table = 'users_user'
        indexes = [
            models.Index(fields=['username'], name='idx_username'),
            models.Index(fields=['email'], name='idx_email'),
            models.Index(fields=['is_deleted'], name='idx_is_deleted'),
            models.Index(fields=['created_at'], name='idx_created_at'),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    def soft_delete(self):
        """Soft delete the user instead of hard delete."""
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=['is_deleted', 'is_active', 'updated_at'])
    
    def restore(self):
        """Restore a soft-deleted user."""
        self.is_deleted = False
        self.is_active = True
        self.save(update_fields=['is_deleted', 'is_active', 'updated_at'])
    
    def get_full_name(self):
        """Return full name or username if not set."""
        full_name = super().get_full_name()
        return full_name if full_name.strip() else self.username
    
    def has_role(self, role_name):
        """Check if user has a specific role."""
        return self.user_roles.filter(
            role__name=role_name, 
            is_deleted=False
        ).exists()
    
    def has_permission(self, permission_name):
        """Check if user has a specific permission through any role."""
        return Permission.objects.filter(
            role_permissions__role__user_roles__user=self,
            role_permissions__role__user_roles__is_deleted=False,
            name=permission_name
        ).exists()
    
    def get_roles(self):
        """Get all active roles for this user."""
        return Role.objects.filter(
            user_roles__user=self,
            user_roles__is_deleted=False,
            is_deleted=False
        )
    
    def get_permissions(self):
        """Get all permissions for this user through roles."""
        return Permission.objects.filter(
            role_permissions__role__user_roles__user=self,
            role_permissions__role__user_roles__is_deleted=False
        ).distinct()


class Role(models.Model):
    """
    Role model for RBAC.
    
    Maps to: users_role table
    
    Predefined roles:
    - admin: Full system access
    - staff: General staff access
    - customer: Customer portal access
    - tailor: Tailoring operations
    - delivery: Delivery operations
    - designer: Design management
    """
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('staff', 'Staff'),
        ('customer', 'Customer'),
        ('tailor', 'Tailor'),
        ('delivery', 'Delivery Personnel'),
        ('designer', 'Designer'),
    ]
    
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users_role'
        indexes = [
            models.Index(fields=['name'], name='idx_role_name'),
            models.Index(fields=['is_deleted'], name='idx_role_is_deleted'),
        ]
    
    def __str__(self):
        return self.name


class UserRole(models.Model):
    """
    Junction table for User-Role many-to-many relationship.
    
    Maps to: users_user_role table
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='user_roles'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.RESTRICT,
        related_name='user_roles'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='role_assignments_made'
    )
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'users_user_role'
        unique_together = ('user', 'role')
        indexes = [
            models.Index(fields=['user'], name='idx_user_role_user'),
            models.Index(fields=['role'], name='idx_user_role_role'),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class Permission(models.Model):
    """
    Permission model for granular access control.
    
    Maps to: users_permission table
    
    Examples:
    - view_orders, edit_orders, delete_orders
    - manage_inventory, view_reports
    - manage_users, manage_roles
    """
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users_permission'
        indexes = [
            models.Index(fields=['name'], name='idx_permission_name'),
        ]
    
    def __str__(self):
        return self.name


class RolePermission(models.Model):
    """
    Junction table for Role-Permission many-to-many relationship.
    
    Maps to: users_role_permission table
    """
    
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='role_permissions'
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='role_permissions'
    )
    
    class Meta:
        db_table = 'users_role_permission'
        unique_together = ('role', 'permission')
        indexes = [
            models.Index(fields=['role'], name='idx_role_perm_role'),
        ]
    
    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"
