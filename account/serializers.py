from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'full_name', 'email', 'image', 'role','language', 'subscription', 'google_id', 'videos_progress',
                'is_active', 'is_staff', 'is_superuser', 'otp', 'otp_expired', 'date_joined', 'last_login']
        read_only_fields = ['user_id', 'date_joined', 'last_login']