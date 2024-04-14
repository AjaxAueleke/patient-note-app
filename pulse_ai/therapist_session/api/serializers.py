from rest_framework import serializers
from pulse_ai.therapist_session.models import TherapistSession

class TherapistSessionSerializer(serializers.ModelSerializer):
    session_audio = serializers.FileField()
    class Meta:
        model = TherapistSession
        fields = ['id', 'session_name', 'session_audio']

    def validate_session_audio(self, value):
        if value.file.size > 1024*1024*5:  # Limit file size to 5MB
            raise serializers.ValidationError("Audio file is too large ( > 5MB ).")
        if not value.file.content_type.startswith('audio/mpeg'):
            raise serializers.ValidationError("Invalid file type. MP3 required.")
        return value




