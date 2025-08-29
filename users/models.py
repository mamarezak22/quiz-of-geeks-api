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


class UserHistory(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    count_of_games = models.IntegerField(default=0)
    count_of_loss_games = models.IntegerField(default=0)
    count_of_won_games = models.IntegerField(default=0)
    count_of_tie_games = models.IntegerField(default=0)