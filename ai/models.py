from django.db import models
import uuid
from account.models import User

class Video(models.Model):
    object_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video_id = models.CharField(max_length=16, unique=True)
    file = models.FileField(upload_to='videos/')
    video_filename = models.CharField(max_length=255, blank=True)
    video_path = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.video_id

class Subtitle(models.Model):
    object_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='subtitles')
    video_filename = models.CharField(max_length=255)
    pdf_filename = models.CharField(max_length=255)
    transcript = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.object_id)

class GlobalPDF(models.Model):
    object_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pdf_id = models.CharField(max_length=16, unique=True)
    pdf_filename = models.CharField(max_length=255)
    pdf_path = models.FilePathField(path='global_pdfs')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.object_id)

class GlobalChatSession(models.Model):
    object_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default="New Session")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.object_id)

class GlobalMessage(models.Model):
    object_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.ForeignKey(GlobalChatSession, on_delete=models.CASCADE)
    role = models.CharField(max_length=10)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.object_id)





