from django.db import models
import uuid

class Video(models.Model):
    object_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video_id = models.CharField(max_length=16, unique=True)
    video_filename = models.CharField(max_length=255)
    video_path = models.FilePathField(path='videos')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.object_id)

class Subtitle(models.Model):
    object_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video_id = models.ForeignKey(Video, on_delete=models.CASCADE)
    video_object_id = models.UUIDField(default=uuid.uuid4, editable=False)
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





