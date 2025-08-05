import random
from users.service import is_phone_number_validated
from utils.validators import validate_phone_number
from django.core.cache import cache
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CheckCodeSerializer, CustomTokenObtainPairSerializer, GetCodeSerializer, PasswordForgotSerialzier, PasswordForgotVerifySerialzier, UserSerializer
from .models import User
from .serializers import RegisterSerializer
from utils.validators import validate_phone_number
from .tasks import send_code

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



class GetCodeView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = GetCodeSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data["phone_number"]
            validate_phone_number(phone)

            if User.objects.filter(phone_number=phone).exists():
                return Response({"detail": "user already registered"}, status=400)

            code = random.randint(100000,999999) 
            #only 2minute for validating the code that been sented.
            cache.set(phone, str(code), timeout=120)
            send_code.delay(phone, code)

            return Response({"detail": "code has been sent"}, status=200)
        
        return Response(serializer.errors,
                        status = 400)


class CheckCodeView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        serializer = CheckCodeSerializer(data = request.data) 

        if serializer.is_valid():
            code = serializer.validated_data["code"] 
            phone_number = serializer.validated_data["phone_number"]

            sended_code = cache.get(phone_number)
            if sended_code != code:
                return Response({"detail" : "code not valid"},
                                status = 400)
            cache.set(f"verified:{phone_number}", True, timeout=600)
            return Response({"detail" : "code valid"},
                            status = 200)
        
        return Response(serializer.errors,
        status = 400)

class RegisterUserView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        serializer = RegisterSerializer(data = request.data)
        if serializer.is_valid():
            if not is_phone_number_validated(serializer.validated_data["phone_number"]) :
                return Response({"detail" : "not validated yet"},
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
        if serializer.is_valid():
            serializer.save()
            return Response({"detail" : "user updated"},
                            status = 200)

        return Response(serializer.errors,
                        status = 400)


class PasswordForgotView(APIView):
   def post(self,request):
        serializer = GetCodeSerializer(data = request.data)

        if serializer.is_valid():
            phone = serializer.validated_data["phone_number"]
            rand_code = random.randint(100000,999999)
            send_code.delay(phone,
                            rand_code)
            cache.set(phone,rand_code,timeout = 120)
            return Response({"detail" : "code has been sended"},
                            status = 200)
        
        return Response(serializer.errors,
                        status = 400)


class PasswordForgotVerifyView(APIView):
    def post(self,request):
        serializer = CheckCodeSerializer(data = request.data)
        user = request.user
        
        if serializer.is_valid():
            phone = serializer.validated_data["phone_number"]
            code = serializer.validated_data["code"]
            cached_code = int(cache.get(phone))
            if not cached_code:
                return Response({"detail" : "code expired"},
                                status = 400)

            if cached_code != code :
                return Response({"detail" : "code is wrong"},
                                status = 400)
            
            #if cached_code == code (the user sends a right code)
            new_password = serializer.validated_data["new_password"]
            user.set_password(new_password)
            user.save()
            return Response({"detail" : "password changed sucsessfully"},
                            status = 200)

                


            
            
     