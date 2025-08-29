from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, AuthUser
from rest_framework_simplejwt.tokens import Token
from rest_framework import serializers

from django.contrib.auth import get_user_model

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: AuthUser) -> Token:
        token = super().get_token(user)
        token["phone_number"] = user.phone_number
        return token

class GetCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length = 12)

class CheckCodeSerializer(serializers.Serializer):
    phone_number =  serializers.CharField(max_length = 12) 
    code = serializers.IntegerField()

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "phone_number", "password",)
        extra_kwargs = {"password": {"write_only": True}}

    #so when you said something like user.save()
    #it triggers the createuser function.
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username","password","phone_number")
        read_only_fields = ["phone_number"]
        extra_kwargs =  {"password": {"write_only": True}}

class ChangePasswordSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length = 12)
    code = serializers.IntegerField(max_length = 6)
    new_password = serializers.CharField()