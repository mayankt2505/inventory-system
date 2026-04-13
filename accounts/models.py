from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.CharField(max_length=255, default="no_image.jpg")
    status = models.BooleanField(default=True)
    legacy_user_level = models.IntegerField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username