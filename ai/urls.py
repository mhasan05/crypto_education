from django.urls import path
from .views import *

urlpatterns = [
    path('upload_video/', UploadVideo.as_view()),
    path("print_collections/", PrintCollections.as_view()),
    path('process_from_file/<str:object_id>/', ProcessFromFileAPIView.as_view()),
    path('ask_question_from_video/<str:video_id>/', VideoQuestionAPIView.as_view(), name='video-question'),
    path('ask_global_question/', GlobalQuestionAPIView.as_view(), name='global-question'),

]
