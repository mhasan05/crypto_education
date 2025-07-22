# urls.py

from django.urls import path
from .views import *

urlpatterns = [
    path('all_notifications/', NotificationListAPIView.as_view(), name='all_notifications'),
    path('unread_notifications/', NotificationUnreadListAPIView.as_view(), name='unread_notifications'),
    path('read/<int:pk>/', NotificationMarkAsReadAPIView.as_view(), name='notification_mark_read'),
    path('read_all/', NotificationMarkAllAsReadAPIView.as_view(), name='notification_mark_all_read'),
]
