from rest_framework import serializers
from pulse_ai.users.models import User  # Import User model
from .models import Patient

class PatientSerializer(serializers.ModelSerializer):
    therapist = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())  # Add therapist field

    class Meta:
        model = Patient
        fields = '__all__'  # Include all fields, including therapist
