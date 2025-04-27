from django.contrib import admin
from django.urls import path,include
from rest_framework_simplejwt.views import TokenRefreshView

from .views import CustomTokenObtainPairView, VerifyPhoneView, GetCodeView, RegisterUserView, GetMeView

urlpatterns = [
    path("auth/token/",CustomTokenObtainPairView.as_view()),
    path("auth/token/refresh",TokenRefreshView.as_view()),
    path("auth/register",RegisterUserView.as_view()),
    path("auth/verify-phone",VerifyPhoneView.as_view()),
    path("auth/get-code",GetCodeView.as_view()),
    path("me",GetMeView.as_view()),
]
