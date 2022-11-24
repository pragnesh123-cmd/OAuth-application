from django.db import models
from django.contrib.auth.models import AbstractUser
import datetime


class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class User(AbstractUser):
    username = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]


class ForgotPasswordToken(TimeStampModel):
    user = models.ForeignKey(
        "User", related_name="reset_tokens", on_delete=models.CASCADE
    )
    token = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        get_latest_by = ("created_at",)

    def __str__(self):
        return f"{self.user} - {self.token}"

    @classmethod
    def has_latest_token(cls, user):
        last_time = datetime.datetime.now() - datetime.timedelta(minutes=5)
        return cls.objects.filter(
            is_active=True, user=user, created_at__lte=last_time
        ).exists()

