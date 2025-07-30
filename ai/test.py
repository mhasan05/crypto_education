from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status,permissions, parsers
from .models import *
import uuid
from .serializers import *
from .utils import *
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.exceptions import NotFound, APIException
from rest_framework.permissions import IsAuthenticated
import random
import string
import uuid
import google.generativeai as genai
import re
from django.db.models import Count
from datetime import datetime, timedelta

@method_decorator(csrf_exempt, name='dispatch')
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
        try:
            pdf_path, pdf_filename, subtitle_object_id = process_video_from_file(video.object_id)
            try:
            # ✅ Fetch subtitle object from PostgreSQL using UUID
                try:
                    subtitle = Subtitle.objects.get(object_id=subtitle_object_id)
                except Subtitle.DoesNotExist:
                    raise NotFound("Subtitle document not found in PostgreSQL")

                pdf_filename = subtitle.pdf_filename
                if not pdf_filename:
                    raise NotFound("PDF filename not found in Subtitle record")

                pdf_path = os.path.join(PDF_FOLDER, pdf_filename)
                print(f"PDF Path: {pdf_path}")
                if not os.path.exists(pdf_path):
                    raise NotFound("PDF file not found on server")

                # ✅ Extract, chunk, and store text
                text = extract_text_from_pdf_path(pdf_path)
                chunks = chunk_text(text)
                store_embeddings_for_pdf(str(subtitle.object_id), chunks)

                try:
                    pdf_path, pdf_filename, subtitle_object_id = process_video_from_file(subtitle.object_id)
                except Exception as e:
                    return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                return Response({
                    "pdf_path": pdf_path,
                    "pdf_filename": pdf_filename,
                    "subtitle_object_id": str(subtitle_object_id),
                    "next_step": f"/api/v1/ai/process_from_file/{subtitle_object_id}/"
                })


            except Exception as e:
                raise APIException(f"Error processing PDF from PostgreSQL: {str(e)}")
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)