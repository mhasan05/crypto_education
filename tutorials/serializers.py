from rest_framework import serializers
from .models import *

class LiveClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveClass
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    total_videos = serializers.SerializerMethodField()
    completed_videos = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'thumbnail', 'total_videos', 'completed_videos']

    def get_total_videos(self, obj):
        return obj.videos.count()

    def get_completed_videos(self, obj):
        user = self.context.get('request').user
        if not user or user.is_anonymous:
            return 0
        return UserVideoProgress.objects.filter(
            user=user,
            video__category=obj,
            is_completed=True
        ).count()


class VideoLessonSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    language_name = serializers.CharField(source='language.name', read_only=True)
    class Meta:
        model = VideoLesson
        fields = ['id', 'title', 'category', 'category_name', 'language', 'language_name', 'video_file', 'duration_seconds', 'order', 'created_at']


class CategoryWithVideosSerializer(serializers.ModelSerializer):
    videos = VideoLessonSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'thumbnail', 'videos']


class UserVideoProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserVideoProgress
        fields = '__all__'


class VideoPlaybackSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoPlayback
        fields = '__all__'
