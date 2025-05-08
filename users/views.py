import random
import uuid
from utils.validators import validate_phone_number
from django.core.cache import cache
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, UserSerializer
from users.services.send_code import send_code
from .models import User
from .serializers import RegisterSerializer
from utils.validators import validate_phone_number

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class GetCodeView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        phone_number = request.data.get('phone_number')
        validate_phone_number(phone_number)
        if User.objects.filter(phone_number=phone_number).exists():
            return Response({"detail" : "user already registered"},
                            status = 400)
        random_code = random.randint(100000, 999999)
        send_code(phone_number,random_code)
        cache.set(phone_number,str(random_code))
        session_token = uuid.uuid4()
        cache.set(session_token,phone_number,timeout = 600)
        return Response({"session_token" : session_token},
                        status= 200)

class VerifyPhoneView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        code = request.data.get('code')
        session_token = request.data.get('session_token')
        phone_number = cache.get(session_token)
        if not phone_number:
            return Response({"detail" : "session token not valid"},
                            status = 400)
        sended_code = cache.get(phone_number)
        if sended_code != code:
            return Response({"detail" : "code not valid"},
                            status = 400)
        cache.set(f"verified_{session_token}",phone_number,timeout = 600)
        return Response({"detail" : "code valid"},
                        status = 200)

class RegisterUserView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        session_token = request.data.get('session_token')
        phone_number = cache.get(f"verified_{session_token}")
        if not phone_number:
            return Response({"detail" : "session token not valid"},
                            status = 400)
        serializer = RegisterSerializer(data = {"phone_number" : phone_number,
                                        "username" : request.data.get('username'),
                                         "password" : request.data.get('password')})

        if serializer.is_valid():
            serializer.save()
            cache.delete(f"verified_{session_token}")
            user = User.objects.get(username = serializer.data['username'])
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