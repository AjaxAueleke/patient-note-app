from rest_framework import serializers
from .models import Favorite
from pulse_ai.users.models import User  # Import the User model if not already imported
from pulse_ai.therapist_session.api.serializers import TherapistSessionSerializer

class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)  # Include the therapist (user) in the response
    favorite = serializers.BooleanField(default=True)  # Add the 'favorite' boolean field
    session = TherapistSessionSerializer(read_only=True) 

    class Meta:
        model = Favorite
        fields = ['id', 'session', 'created_at', 'user', 'favorite']  # Include 'favorite' in the fields
