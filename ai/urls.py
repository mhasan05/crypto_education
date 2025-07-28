from django.urls import path
from .views import *

urlpatterns = [
    path('upload_video/', UploadVideo.as_view()),
    path("print_collections/", PrintCollections.as_view()),
    path('process_from_file/<str:object_id>/', ProcessFromFileAPIView.as_view()),
    # path('ask_question_from_video/<str:video_id>/', VideoQuestionAPIView.as_view(), name='video-question'),
    # path('ask_global_question/', GlobalQuestionAPIView.as_view(), name='global-question'),
    path("load_pdf_postgres_to_chroma/<uuid:object_id>/", LoadPDFPostgresToChroma.as_view()),
    path("create_video_chat_session/", CreateVideoChatSession.as_view()),
    path("ask_question_from_video/<uuid:object_id>/", AskQuestionFromVideo.as_view()),
    path("upload_global_pdf/", UploadGlobalPDFView.as_view(), name="upload-global-pdf"),
    path("create_session/", CreateGlobalChatSessionView.as_view(), name="create-global-session"),
    path("ask_global_question/", AskGlobalQuestionAPIView.as_view(), name="ask_global_question"),
    path("session_messages/<uuid:session_id>/", SessionMessagesAPIView.as_view(), name="session_messages"),
    path("global_session/", GlobalSessionAPIView.as_view(), name="global_session"),
    path("rename_global_session/<uuid:session_id>/", RenameGlobalChatSessionAPIView.as_view(), name="rename_global_session"),

]
