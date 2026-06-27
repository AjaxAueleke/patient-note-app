from typing import ClassVar

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.db.models import EmailField
from django.db.models import ImageField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field

from pulse_ai.therapist_session.s3_client import S3Client
from .managers import UserManager


class User(AbstractUser):
    """
    Default custom user model for pulse-ai.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]
    profile_picture = ImageField(_("Profile Picture"), upload_to='profile_pics/', blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})

    @extend_schema_field(str)
    def get_profile_picture_url(self):
        if not self.profile_picture:
            return None
        s3_client = S3Client.get_instance()
        try:
            signed_url = s3_client.generate_presigned_url('get_object',
                                                          Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                                  'Key': f'media/{self.profile_picture.name}', },
                                                          ExpiresIn=3600 * 24 * 6)  # URL expires in 6 days
            return signed_url
        except Exception:
            return None
