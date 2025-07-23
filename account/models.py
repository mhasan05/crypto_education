from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from account.manager import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    LANGUAGE_CHOICES = [
        ('english', 'English'),
        ('german', 'German'),
    ]
    class Meta:
        verbose_name_plural = "Users"
    user_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True)
    image = models.ImageField(upload_to='profile_images', default='profile_images/default.jpg')
    google_image_url = models.URLField(blank=True, null=True)
    role = models.CharField(max_length=20, default='user')
    language = models.CharField(max_length=20,choices=LANGUAGE_CHOICES,default='english')
    subscription = models.CharField(max_length=20, default='free')
    google_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    videos_progress = models.JSONField(default=dict,null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expired = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(auto_now=True)

    @property
    def image_url(self):
        if self.google_image_url:
            return self.google_image_url
        else:
            return self.image.url

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = UserManager()


    def __str__(self):
        return str(self.full_name)
