from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from notifications.models import Notification
from .models import *
from .serializers import *


class LiveClassListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        classes = LiveClass.objects.all().order_by('-date_time')
        serializer = LiveClassSerializer(classes, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = LiveClassSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LiveClassRetrieveUpdateDeleteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return LiveClass.objects.get(pk=pk)
        except LiveClass.DoesNotExist:
            return None

    def get(self, request, pk):
        live_class = self.get_object(pk)
        if not live_class:
            return Response({"status": "error", "message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = LiveClassSerializer(live_class)
        return Response({"status": "success", "data": serializer.data})

    def put(self, request, pk):
        live_class = self.get_object(pk)
        if not live_class:
            return Response({"status": "error", "message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = LiveClassSerializer(live_class, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data})
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        live_class = self.get_object(pk)
        if not live_class:
            return Response({"status": "error", "message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        live_class.delete()
        return Response({"status": "success", "message": "Live class deleted successfully"})



class CategoryListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True, context={'request': request})
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                    "status": "success",
                    "data": serializer.data,
                }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        return get_object_or_404(Category, pk=pk)

    def get(self, request, pk):
        category = self.get_object(pk)
        serializer = CategorySerializer(category)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        category = self.get_object(pk)
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            "status": "error",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        category = self.get_object(pk)
        category.delete()
        return Response({
            "status": "success",
            "data": "Category deleted successfully"
        }, status=status.HTTP_200_OK)


class VideoLessonListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        user = request.user
        if not user.is_superuser:
            videos = VideoLesson.objects.filter(language__name=user.language)
        else:
            videos = VideoLesson.objects.all()
        serializer = VideoLessonSerializer(videos, many=True)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = VideoLessonSerializer(data=request.data)
        if serializer.is_valid():
            video = serializer.save()

            # Trigger notification
            users = User.objects.all()
            notifications = [
                Notification(
                    user=user,
                    video=video,
                    message=f"New video uploaded in {video.category.name}: {video.title}"
                )
                for user in users
            ]
            Notification.objects.bulk_create(notifications)

            return Response({
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": "error",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class CategoryWiseVideoListAPIView(APIView):
    def get(self, request):
        categories = Category.objects.prefetch_related('videos').all()
        serializer = CategoryWithVideosSerializer(categories, many=True)
        return Response({
            "status": "success",
            "data": serializer.data
        })
    
class SingleCategoryVideoAPIView(APIView):
    def get(self, request, category_id):
        try:
            category = Category.objects.prefetch_related('videos').get(id=category_id)
        except Category.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Category not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CategoryWithVideosSerializer(category)
        return Response({
            "status": "success",
            "data": serializer.data
        })

class VideoLessonDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        return get_object_or_404(VideoLesson, pk=pk)

    def get(self, request, pk):
        video = self.get_object(pk)
        serializer = VideoLessonSerializer(video)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        video = self.get_object(pk)
        serializer = VideoLessonSerializer(video, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            "status": "error",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        video = self.get_object(pk)
        video.delete()
        return Response({
            "status": "success",
            "data": "Video deleted successfully"
        }, status=status.HTTP_200_OK)




class UserVideoProgressAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        progress = UserVideoProgress.objects.filter(user=request.user)
        serializer = UserVideoProgressSerializer(progress, many=True)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserVideoProgressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        video_id = request.data.get('video')
        instance = get_object_or_404(UserVideoProgress, user=request.user, video_id=video_id)
        serializer = UserVideoProgressSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            "status": "error",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



class VideoPlaybackAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        playback = VideoPlayback.objects.filter(user=request.user)
        serializer = VideoPlaybackSerializer(playback, many=True)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = VideoPlaybackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        video_id = request.data.get('video')
        instance = get_object_or_404(VideoPlayback, user=request.user, video_id=video_id)
        serializer = VideoPlaybackSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            "status": "error",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
