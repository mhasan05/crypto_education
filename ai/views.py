from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status,permissions
from .models import *
import uuid
from .serializers import *
from .utils import *
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator



class UploadVideo(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get("video")
        if not file:
            return Response({"detail": "No video file uploaded."}, status=400)

        video_id = str(uuid.uuid4())[:8]

        # Create video entry with file
        video = Video.objects.create(
            video_id=video_id,
            file=file,
        )

        # Save filename and path after file is uploaded
        video.video_filename = video.file.name.split('/')[-1]
        video.video_path = video.file.name  # This is relative to MEDIA_ROOT
        video.save()

        return Response({
            "message": "Video uploaded successfully",
            "video_id": video.video_id,
            "object_id": str(video.object_id),
            "video_filename": video.video_filename,
            "video_path": video.video_path,
            "next_step": f"/api/v1/ai/process_video/{video.object_id}/"
        })
    


class PrintCollections(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        videos = Video.objects.all()
        subtitles = Subtitle.objects.all()

        video_data = VideoSerializer(videos, many=True).data
        subtitle_data = SubtitleSerializer(subtitles, many=True).data

        return Response({
            "videos": video_data,
            "subtitles": subtitle_data
        })
    

@method_decorator(csrf_exempt, name='dispatch')
class ProcessFromFileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, object_id):
        try:
            pdf_path, pdf_filename, subtitle_object_id = process_video_from_file(object_id)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "pdf_path": pdf_path,
            "pdf_filename": pdf_filename,
            "subtitle_object_id": str(subtitle_object_id)
        })


class GlobalQuestionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        question = request.data.get("question")
        if not question:
            return Response({"detail": "Question is required."}, status=400)
        return Response({"answer": "This is a sample answer to your question."})
    

class VideoQuestionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, video_id=None):
        question = request.data.get("question")
        if not question:
            return Response({"detail": "Question is required."}, status=400)
        return Response({"answer": "This is a sample answer to your question."})