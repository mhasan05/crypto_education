from django.urls import path
from .views import *

urlpatterns = [
    path('live_classes/', LiveClassListCreateAPIView.as_view(), name='live_class_list_create'),
    path('live_classes_update', LiveClassRetrieveUpdateDeleteAPIView.as_view(), name='live_class'),
    path('courses/', CourseListCreateAPIView.as_view()),
    path('courses/<int:pk>/', CourseDetailAPIView.as_view()),

    path('categories/', CategoryListCreateAPIView.as_view()),
    path('categories/<int:pk>/', CategoryDetailAPIView.as_view()),
    path('videos/', VideoLessonListCreateAPIView.as_view()),
    path('videos/<str:pk>/', VideoLessonDetailAPIView.as_view()),
    path('category_videos/', CategoryWiseVideoListAPIView.as_view(), name='category_videos'),
    path('category_videos/<int:category_id>/', SingleCategoryVideoAPIView.as_view(), name='category_video_detail'),
    path('progress/', UserVideoProgressAPIView.as_view()),
    path('playback/', VideoPlaybackAPIView.as_view()),
]
