from django.contrib.auth.models import UserManager

class UserManager(UserManager):
    def _create_user(self, phone_number, password, **extra_fields):
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_user(self, phone_number, password, **extra_fields):
        return self._create_user(phone_number, password, **extra_fields)
    def create_superuser(self, phone_number, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        return self._create_user(phone_number, password, **extra_fields)