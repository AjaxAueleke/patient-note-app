import boto3
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from drf_spectacular.utils import extend_schema_field

from pulse_ai.therapist_session.validators import validate_audio_mime_type
from pulse_ai.users.models import User


class TherapistSession(models.Model):
    therapist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='therapist_sessions')
    session_name = models.CharField(max_length=50, blank=False, null=False, validators=[MinLengthValidator(5)])
    session_audio = models.FileField(upload_to='sessions/', validators=[validate_audio_mime_type])
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.session_name} by {self.therapist.username}"

    @extend_schema_field(str)
    def get_session_audio_url(self):
        if not self.session_audio:
            return None
        s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                 aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                 region_name=settings.AWS_S3_REGION_NAME)
        try:
            signed_url = s3_client.generate_presigned_url('get_object',
                                                          Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                                  'Key': f'media/{self.session_audio.name}', },
                                                          ExpiresIn=3600 * 24 * 6)  # URL expires in 1 hour
            return signed_url
        except Exception as e:
            return None


class Transcription(models.Model):
    session = models.ForeignKey(TherapistSession, on_delete=models.CASCADE, related_name='transcriptions')
    transcription_text_file = models.FileField(upload_to='transcriptions/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class Summary(models.Model):
    session = models.ForeignKey(TherapistSession, on_delete=models.CASCADE, related_name='summaries')
    summary_text_file = models.FileField(upload_to='summaries/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class Error(models.Model):
    session = models.ForeignKey(TherapistSession, on_delete=models.CASCADE, related_name='errors')
    error_message = models.TextField()
    error_code = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
