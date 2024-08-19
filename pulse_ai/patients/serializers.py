from rest_framework import serializers
from .models import Patient

class PatientSerializer(serializers.ModelSerializer):
    # Remove therapist from the list of fields exposed to the API
    therapist = serializers.PrimaryKeyRelatedField(read_only=True)  # Make it read-only if you want to include it in the response

    class Meta:
        model = Patient
        fields = '__all__'  # Include all fields, therapist will be set automatically
