# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Feedback
from .serializers import FeedbackSerializer
from django.shortcuts import get_object_or_404

class FeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        feedbacks = Feedback.objects.filter(user=request.user)
        serializer = FeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, object_id):
        feedback = get_object_or_404(Feedback, object_id=object_id, user=request.user)
        serializer = FeedbackSerializer(feedback, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)  # reassign user just in case
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, object_id):
        feedback = get_object_or_404(Feedback, object_id=object_id, user=request.user)
        feedback.delete()
        return Response({"detail": "Feedback deleted"}, status=status.HTTP_200_OK)
