from django.db import models

class Patient(models.Model):
    name = models.CharField(max_length=255)  # Name is required
    age = models.IntegerField(null=True, blank=True)  # Optional
    description = models.TextField(null=True, blank=True)  # Optional
    gender = models.CharField(max_length=10, null=True, blank=True)  # Optional
    phone = models.CharField(max_length=20, null=True, blank=True)  # Optional
    dob = models.DateField(null=True, blank=True)  # Optional

    def __str__(self):
        return self.name
