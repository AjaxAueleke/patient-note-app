from django.db import models
from pulse_ai.users.models import User

class TherapistSession(models.Model):

    therapist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='therapist_sessions')
    session_name = models.CharField(max_length=255)
    session_audio = models.FileField(upload_to='sessions/')

    def __str__(self):
        return f"{self.session_name} by {self.therapist.username}"

    class Meta:
        app_label = 'patient_note_app.therapist_sessions'


