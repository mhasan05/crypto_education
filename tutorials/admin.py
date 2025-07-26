from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Category)
admin.site.register(VideoLesson)
admin.site.register(UserVideoProgress)
admin.site.register(VideoPlayback)
admin.site.register(Language)
admin.site.register(LiveClass)
