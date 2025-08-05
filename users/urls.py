from django.contrib import admin
from django.urls import path,include
from rest_framework_simplejwt.views import TokenRefreshView

from .views import CheckCodeView, CustomTokenObtainPairView , GetCodeView, PasswordForgotVerifyView, PasswordForgotView, RegisterUserView,UserDetailView 

urlpatterns = [
    path("token/",CustomTokenObtainPairView.as_view()),
    path("token/refresh/",TokenRefreshView.as_view()),
    path("register/",RegisterUserView.as_view()),
    path("check-code/",CheckCodeView.as_view()),
    path("get-code/",GetCodeView.as_view()),
    path("me/",UserDetailView.as_view()),
    path("pass-forgot/",PasswordForgotView.as_view()),
    path("change-pass/",PasswordForgotVerifyView.as_view()),
]

