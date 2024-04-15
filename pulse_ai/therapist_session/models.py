from django.db import models
from pulse_ai.users.models import User
from pulse_ai.therapist_session.validators import validate_audio_mime_type

class TherapistSession(models.Model):
    SESSION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('transcribed', 'Transcribed'),
        ('done', 'Done'),
    ]
    therapist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='therapist_sessions')
    session_name = models.CharField(max_length=255)
    session_audio = models.FileField(upload_to='sessions/', validators=[validate_audio_mime_type])
    session_status = models.CharField(max_length=11, choices=SESSION_STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.session_name} by {self.therapist.username}"
