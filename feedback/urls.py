# urls.py
from django.urls import path
from .views import FeedbackView

urlpatterns = [
    path('feedback/', FeedbackView.as_view(), name='feedback-list-post'),
    path('feedback/<uuid:object_id>/', FeedbackView.as_view(), name='feedback-update-delete'),
]
