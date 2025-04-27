from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from utils.validators import validate_phone_number

from .managers import UserManager

class User(AbstractBaseUser):
    phone_number = models.CharField(max_length=11, unique=True,validators=[validate_phone_number],db_index = True)
    username = models.CharField(max_length=32,unique = True,db_index = True)
    last_login = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username
