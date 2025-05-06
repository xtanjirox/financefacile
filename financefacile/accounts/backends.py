from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()

class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using their email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None
            
        try:
            # Check if the provided username is actually an email
            # Try to find the user by either username or email
            user = User.objects.filter(
                Q(username=username) | Q(email=username)
            ).first()
            
            # Check if we got a user and if the password is correct
            if user and user.check_password(password):
                return user
                
        except Exception as e:
            # Handle any unexpected errors
            print(f"Error in email authentication: {e}")
            return None
            
        # Run the default password hasher once to reduce the timing
        # difference between an existing and a nonexistent user
        User().set_password(password)
        return None
