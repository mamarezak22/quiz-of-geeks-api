import random
from utils.validators import validate_phone_number
from django.core.cache import cache
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CheckCodeSerializer, CustomTokenObtainPairSerializer, GetCodeSerializer, ChangePasswordSerializer , UserSerializer, RegisterSerializer
from .tasks import send_code
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



class GetCodeView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = GetCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]
        validate_phone_number(phone)

        if User.objects.filter(phone_number=phone).exists():
            return Response({"detail": "user already registered"}, status=400)

        code = random.randint(100000,999999) 

        #only 2minute for validating the code that been sented.
        cache.set(f"code for {phone}", str(code), timeout=120)
        send_code.delay(phone, code)

        return Response({"detail": "code has been sent"}, status=200)

class CheckCodeView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        serializer = CheckCodeSerializer(data = request.data) 
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"] 
        phone_number = serializer.validated_data["phone_number"]

        sended_code = cache.get(f"code for {phone_number}")

        if not sended_code:
            return Response({"detail" : "code expired"},
            status = 400)

        elif sended_code != code:
            return Response({"detail" : "code not valid"},
                            status = 400)
        cache.set(f"{phone_number} verified", True)
        return Response({"detail" : "code valid"},
                        status = 200)

class RegisterUserView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        serializer = RegisterSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]
        phone_number_verified = cache.get(f"{phone_number} verified") 

        if not phone_number_verified:
            return Response({"detail" : "phone number not validated yet"},
                            status = 400)

        user = serializer.save()
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        return Response({
            "refresh" : str(refresh),
            "access" : str(refresh.access_token),
        },status = 201)

class UserDetailView(APIView):
    def get(self,request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data , 
                        status = 200)
    def patch(self,request):
        serializer = UserSerializer(request.user,
                                    data = request.data,
                                    partial = True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail" : "user updated"},
                        status = 200)



class PasswordForgotGetCodeView(APIView):
   def post(self,request):
        serializer = GetCodeSerializer(data = request.data)

        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]
        rand_code = random.randint(100000,999999)
        send_code.delay(phone,
                        rand_code)
        cache.set(f"code for {phone}",rand_code,timeout = 120)
        return Response({"detail" : "code has been sent"},
                        status = 200)
        


class PasswordForgotCheckCodeView(APIView):
    def post(self,request):
        serializer = ChangePasswordSerializer(data = request.data)
        user = request.user

        serializer.is_valid(raise_exception=True) 
        phone = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]
        new_pass = serializer.validated_data["new_password"]

        cached_code = int(cache.get(phone))
        if not cached_code:
            return Response({"detail" : "code expired"},
                            status = 400)

        elif cached_code != code :
            return Response({"detail" : "code not valid"},
                            status = 400)
        
        user.set_password(new_pass)
        user.save()
        return Response({"detail" : "password changed sucsessfully"},
                        status = 200)
        
        
    