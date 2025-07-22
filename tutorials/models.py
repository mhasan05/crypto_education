from django.db import models
from account.models import User
from storages.backends.s3boto3 import S3Boto3Storage

s3 = S3Boto3Storage()

class LiveClass(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    date_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='category_thumbnails/', blank=True, null=True, storage=s3)

    def __str__(self):
        return self.name
    

class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    

# Dynamic path generator
def video_upload_path(instance, filename):
    language_folder = instance.language.name.lower().replace(' ', '_')
    return f"videos/{language_folder}/{filename}"



class VideoLesson(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    video_file = models.FileField(upload_to=video_upload_path, blank=True, null=True, storage=s3)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.category.name} - {self.title}"


class UserVideoProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='video_progress')
    video = models.ForeignKey(VideoLesson, on_delete=models.CASCADE, related_name='progress')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'video')

    def __str__(self):
        return f"{self.user.full_name} - {self.video.title} - {'Completed' if self.is_completed else 'In Progress'}"
    


class VideoPlayback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(VideoLesson, on_delete=models.CASCADE)
    # Track how many seconds watched
    seconds_watched = models.PositiveIntegerField(default=0)
    # Resume from this point
    last_watched_second = models.PositiveIntegerField(default=0)
    # Optional: allow user to create a manual bookmark
    bookmarked_second = models.PositiveIntegerField(null=True, blank=True)
    # Track when it was last updated
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'video')

    def __str__(self):
        return f"{self.user.full_name} - {self.video.title} - Watched: {self.seconds_watched}s"

