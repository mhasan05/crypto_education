from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = User
        fields = ['user_id', 'full_name', 'email', 'image', 'role','language', 'subscription', 'google_id', 'videos_progress',
                'is_active', 'is_staff', 'is_superuser', 'otp', 'otp_expired', 'date_joined', 'last_login']
        read_only_fields = ['user_id', 'date_joined', 'last_login']



    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')

        if instance.google_image_url:
            data['image'] = instance.google_image_url
        
        elif instance.image and hasattr(instance.image, 'url'):
            image_url = instance.image.url
            data['image'] = request.build_absolute_uri(image_url) if request else image_url
        else:
            data['image'] = None

        return data