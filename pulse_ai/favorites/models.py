from django.db import models
from pulse_ai.users.models import User
from pulse_ai.therapist_session.models import TherapistSession

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    session = models.ForeignKey(TherapistSession, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'session')

    def __str__(self):
        return f"{self.user.username} - {self.session.session_name}"