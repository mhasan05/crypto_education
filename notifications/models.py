from django.db import models
from django.utils import timezone
from account.models import User
from tutorials.models import VideoLesson

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    video = models.ForeignKey(VideoLesson, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.full_name} - {self.video.title[:30]} - {'Read' if self.is_read else 'Unread'}"
