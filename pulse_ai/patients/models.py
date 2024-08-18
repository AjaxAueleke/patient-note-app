from django.db import models
from pulse_ai.users.models import User

class Patient(models.Model):
    name = models.CharField(max_length=255)  # Name is required
    age = models.IntegerField(null=True, blank=True)  # Optional
    description = models.TextField(null=True, blank=True)  # Optional
    gender = models.CharField(max_length=10, null=True, blank=True)  # Optional
    phone = models.CharField(max_length=20, null=True, blank=True)  # Optional
    dob = models.DateField(null=True, blank=True)  # Optional
    therapist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patients' , null=True , blank=True)  # Foreign key to User model


    def __str__(self):
        return self.name
