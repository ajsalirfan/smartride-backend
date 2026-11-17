from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
    Custom backend — login using either email or username.
    Includes debug prints for testing.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        print(f"🔍 DEBUG: Received login attempt for '{username}'")

        if username is None:
            username = kwargs.get('email')
            print(f"🔄 Using email fallback: {username}")

        try:
            user = User.objects.get(Q(email__iexact=username) | Q(username__iexact=username))
            print(f"✅ Found user: {user.username} ({user.email})")
        except User.DoesNotExist:
            print("❌ No user found matching email or username")
            return None

        if user.check_password(password):
            print("🔓 Password correct — authenticated successfully!")
            return user
        else:
            print("🚫 Incorrect password")
        return None
