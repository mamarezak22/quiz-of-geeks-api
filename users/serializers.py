from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, AuthUser
from rest_framework_simplejwt.tokens import Token
from rest_framework.serializers import ModelSerializer

from .models import User

class RegisterSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "phone_number", "password",)
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("username","password","phone_number")
        read_only_fields = ["phone_number"]
        extra_kwargs =  {"password": {"write_only": True}}

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: AuthUser) -> Token:
        token = super().get_token(user)
        token["phone_number"] = user.phone_number
        return token
