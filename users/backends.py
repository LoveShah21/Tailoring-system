"""
Users App - Authentication Backends

Custom backend supporting login with username OR email.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend that allows login with either username or email.
    
    Usage:
        Add to AUTHENTICATION_BACKENDS in settings.py:
        AUTHENTICATION_BACKENDS = ['users.backends.EmailOrUsernameBackend']
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user by username or email.
        
        Args:
            request: HTTP request object
            username: Username or email provided by user
            password: Password provided by user
        
        Returns:
            User object if credentials are valid, None otherwise
        """
        if username is None or password is None:
            return None
        
        try:
            # Try to find user by username OR email
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except User.DoesNotExist:
            # Run the default password hasher to mitigate timing attacks
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # If somehow there are duplicate emails, try exact username match
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None
        
        # Check password and if user can authenticate
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        """Get user by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
