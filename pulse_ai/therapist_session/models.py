from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from drf_spectacular.utils import extend_schema_field
from patients.models import Patient

from pulse_ai.therapist_session.s3_client import S3Client
from pulse_ai.users.models import User


class TherapistSession(models.Model):
    STATUS_CHOICES = (('pending', 'Pending'), ('done', 'Done'), ('failed', 'Failed'),)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', blank=False, null=False)
    therapist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='therapist_sessions')
    session_name = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(null=True, blank=False)  # Add this line if not present
    session_audio = models.FileField(upload_to='sessions/')
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='sessions', null = False, blank=False)
    summary_regeneration_count = models.PositiveIntegerField(default=0)
    transcription_regeneration_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.session_name} by {self.therapist.username}"

    @extend_schema_field(str)
    def get_session_audio_url(self):
        if not self.session_audio:
            return None
        s3_client = S3Client.get_instance()
        try:
            signed_url = s3_client.generate_presigned_url('get_object',
                                                          Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                                  'Key': f'media/{self.session_audio.name}', },
                                                          ExpiresIn=3600 * 24 * 6)  # URL expires in 1 hour
            return signed_url
        except Exception as e:
            return None


    def can_regenerate_summary(self):
        return self.summary_regeneration_count < settings.MAX_SUMMARY_REGENERATIONS

    def can_regenerate_transcription(self):
        return self.transcription_regeneration_count < settings.MAX_TRANSCRIPTION_REGENERATIONS


class Transcription(models.Model):
    session = models.ForeignKey(TherapistSession, on_delete=models.CASCADE, related_name='transcriptions')
    transcription_text_file = models.FileField(upload_to='transcriptions/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def get_transcription_url(self):
        if not self.transcription_text_file:
            return None

        s3_client = S3Client.get_instance()
        try:
            signed_url = s3_client.generate_presigned_url('get_object',
                                                          Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                                  'Key': f'media/{self.transcription_text_file.name}'},
                                                          ExpiresIn=3600)  # URL expires in 1 hour
            return signed_url
        except Exception as e:
            return None


class Summary(models.Model):
    session = models.ForeignKey(TherapistSession, on_delete=models.CASCADE, related_name='summaries')
    summary_text_file = models.FileField(upload_to='summaries/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def get_summary_url(self):
        if not self.summary_text_file:
            return None
        s3_client = S3Client.get_instance()
        try:
            signed_url = s3_client.generate_presigned_url('get_object',
                                                          Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                                  'Key': f'media/{self.summary_text_file.name}'},
                                                          ExpiresIn=3600)  # URL expires in 1 hour
            return signed_url
        except Exception as e:
            return None


class Error(models.Model):
    session = models.ForeignKey(TherapistSession, on_delete=models.CASCADE, related_name='errors')
    error_message = models.TextField()
    error_code = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
