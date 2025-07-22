from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    video_title = serializers.CharField(source='video.title', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'video', 'video_title', 'message', 'is_read', 'created_at']
