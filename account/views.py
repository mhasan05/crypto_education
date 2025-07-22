from rest_framework.views import APIView
from account.models import User
from rest_framework.response import Response
from rest_framework import status
from .send_otp import send_otp
import random
from django.utils import timezone
from datetime import timedelta
import string
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings

google_client_id = settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
# Create your views here.
class RegisterView(APIView):
    """
    Handle user Register.
    """
    def post(self, request):
        full_name = request.data.get('full_name')
        email = request.data.get('email')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')

        if not email or not password :
            return Response({'status':'error',"message": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        elif User.objects.filter(email=email).exists():
            return Response({'status':'error',"message": "The email is already taken."}, status=status.HTTP_400_BAD_REQUEST)

        elif password != confirm_password:
            return Response({'status':'error',"message": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            pass
        send_email = False
        user = User(full_name=full_name,email=email)
        otp = ''.join(random.choices(string.digits, k=6))
        try:
            user.set_password(password)
            user.otp = otp
            user.otp_expired = timezone.now() + timedelta(minutes=5)
            user.save()
            send_email = send_otp(email, otp)
        except:
            return Response({'status':'error',"message": "Failed to create user. Please try again."}, status=status.HTTP_400_BAD_REQUEST)
        
        if send_email:
            return Response({
            'status': 'success',
            'message': 'Please check your email to get verification code.',
        }, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'error',"message": "Failed to send OTP email. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({"error": "Both email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)
        if user.otp != otp:
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        elif timezone.now() > user.otp_expired:
            return Response({"error": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)
        elif str(user.otp) == otp:
            user.is_active = True
            user.save()
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response(
                {"status": "success", "access_token": access_token, "message": "Email verified successfully."},
                status=status.HTTP_200_OK,
            )
        


class SendOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)
        
        otp = ''.join(random.choices(string.digits, k=6))
        user.otp = otp
        user.otp_expired = timezone.now() + timedelta(minutes=5)
        user.save()
        send_email = send_otp(email, otp)  # Assuming `send_otp` handles sending the OTP via email

        if send_email:
            return Response(
                {"status": "success", "message": "We sent you an OTP to your email."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"status": "error", "message": "Failed to send OTP email. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class LoginView(APIView):
    """
    Handle user login.
    """
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'status': 'error',"message": "Both email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, email=email, password=password)


        if user is None:
            return Response({'status': 'error', "message": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        
        elif not user.is_active:
            return Response({'status':'error', "message": "Please verify your email address."})


        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        return Response({
            'status': 'success',
            'access_token': str(access_token),
            'data': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

class GoogleLoginAPIView(APIView):
    def post(self, request):
        token = request.data.get('id_token')
        if not token:
            return Response({'detail': 'Missing id_token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), google_client_id)

            email = idinfo.get('email')
            full_name = idinfo.get('name') or f"{idinfo.get('given_name', '')} {idinfo.get('family_name', '')}".strip()
            picture = idinfo.get('picture', '')

            if not email:
                return Response({'detail': 'Email not found in token'}, status=status.HTTP_400_BAD_REQUEST)

            user, created = User.objects.get_or_create(email=email)

            if created:
                user.full_name = full_name
                user.image = picture if picture else 'default.jpg'
                user.is_active = True
                user.google_id = idinfo.get('sub')
                user.set_unusable_password()
                user.save()

            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                }
            })

        except ValueError:
            return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

class AdminLoginView(APIView):
    """
    Handle user login.
    """
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'status': 'error',"message": "Both email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, email=email, password=password)

        if user.is_superuser is False:
            return Response({'status': 'error', "message": "You are not authorized to access this resource."}, status=status.HTTP_403_FORBIDDEN)

        if user is None:
            return Response({'status': 'error', "message": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'status': 'error', "message": "Your account is inactive."}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        return Response({
            'status': 'success',
            'access_token': str(access_token),
            'data': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        email = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not old_password or not new_password or not confirm_password:
            return Response(
                {'status': 'error', "message": "Please provide all required password fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != confirm_password:
            return Response(
                {'status': 'error', "message": "New passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(email=email, password=old_password)
        if user is None:
            return Response(
                {'status': 'error', "message": "Invalid old password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {'status': 'success', "message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class ForgotPasswordView(APIView):
    permission_classes = [IsAuthenticated]  # Adjust permission as per your requirement
    def post(self, request):
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        if not new_password or not confirm_password:
            return Response(
                {'status': 'error', "message": "All field are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif new_password != confirm_password:
            return Response(
                {'status': 'error', "message": "password do not match"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif new_password == confirm_password:
            user = request.user
            user.set_password(new_password)
            user.save()
            return Response(
                {'status': 'success', "message": "successfully reset password"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {'status': 'error', "message": "something went wrong."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
            try:
                user_profile = request.user
                serializer = UserSerializer(user_profile)
                return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'status': 'error',"message": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)
        

    def put(self, request):
        user = request.user
        data = request.data.copy()

        # Only allow admin to change restricted fields
        restricted_fields = ['is_superuser','is_staff', 'role', 'otp','is_active', 'otp_expired', 'subscription', 'google_id', 'videos_progress']
        if not user.is_superuser:
            for field in restricted_fields:
                data.pop(field, None)

        serializer = UserSerializer(user, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        user.delete()
        return Response({"status": "success", "message": "User account deleted successfully."}, status=status.HTTP_200_OK)
    


class CustomerView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            try:
                customer = User.objects.get(pk=pk)
                serializer = UserSerializer(customer)
                return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"status": "error", "message": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

        customers = User.objects.all()
        all_customers = User.objects.all().count()
        serializer = UserSerializer(customers, many=True)
        return Response({"status": "success", "total": all_customers, "data": serializer.data}, status=status.HTTP_200_OK)


    def delete(self, request, pk=None):
        try:
            customer = User.objects.get(pk=pk)
            customer.delete()
            return Response({"status": "success", "message": "Customer deleted successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"status": "error", "message": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)