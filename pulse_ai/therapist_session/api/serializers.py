import magic
from rest_framework import serializers

from pulse_ai.therapist_session.models import TherapistSession, Error, Transcription, Summary


class ErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Error
        fields = ['error_message', 'error_code', 'timestamp']


class SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Summary
        fields = ['summary_text_file_url', 'created_at']


class TranscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcription
        fields = ['transcription_text_file_url', 'created_at']


class TherapistSessionSerializer(serializers.ModelSerializer):
    session_audio = serializers.FileField()
    session_audio_url = serializers.SerializerMethodField()
    errors = ErrorSerializer(many=True, read_only=True, source='errors_set')
    summaries = SummarySerializer(many=True, read_only=True, source='summaries_set')
    transcriptions = TranscriptionSerializer(many=True, read_only=True, source='transcriptions_set')

    class Meta:
        model = TherapistSession
        fields = ['id', 'session_name', 'session_audio', 'session_audio_url', 'errors', 'summaries', 'transcriptions']

    def get_session_audio_url(self, obj):
        return obj.get_session_audio_url()

    def validate_session_audio(self, value):
        # Existing validation logic
        if value.size > 1024 * 1024 * 50:
            raise serializers.ValidationError("Audio file is too large ( > 50MB ).")
        if not value.content_type.startswith('audio/mpeg'):
            raise serializers.ValidationError("Invalid file type. MP3 required.")
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(value.read(2048))
        if not mime_type.startswith('audio'):
            raise serializers.ValidationError('This file is not an audio file.')
        value.seek(0)
        return value
