from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from utils.validators import validate_phone_number

from .managers import UserManager

class User(AbstractBaseUser):
    phone_number = models.CharField(max_length=11, unique=True,validators=[validate_phone_number])
    username = models.CharField(max_length=32,unique = True,db_index = True)
    last_login = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    #for acsessing to admin site by admin.
    def has_perm(self, perm, obj=None):
        return self.is_superuser
    def has_module_perms(self, app_label):
        return self.is_superuser
