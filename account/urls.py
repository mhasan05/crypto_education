from django.urls import path
from account import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify_email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('send_otp/', views.SendOtpView.as_view(), name='send_otp'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('admin_login/', views.AdminLoginView.as_view(), name='admin_login'),
    path('change_password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('forgot_password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('user_profile/', views.UserProfileView.as_view(), name='user_profile'),

    path('user_details/', views.CustomerView.as_view(), name='user_details'),
    path('user_details/<int:pk>/', views.CustomerView.as_view(), name='single_user_details'),
]
