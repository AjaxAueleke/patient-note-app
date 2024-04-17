from django.core.validators import MinLengthValidator
from django.db import models

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


class Transcription(models.Model):
    session = models.ForeignKey(TherapistSession, on_delete=models.CASCADE, related_name='transcriptions')
    transcription_text_file_url = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


class Summary(models.Model):
    session = models.ForeignKey(TherapistSession, on_delete=models.CASCADE, related_name='summaries')
    summary_text_file_url = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


class Error(models.Model):
    session = models.ForeignKey(TherapistSession, on_delete=models.CASCADE, related_name='errors')
    error_message = models.TextField()
    error_code = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
