import magic
from rest_framework import serializers

from pulse_ai.therapist_session.models import TherapistSession, Error, Transcription, Summary


class ErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Error
        fields = ['error_message', 'error_code', 'timestamp', 'session']


class SummarySerializer(serializers.ModelSerializer):
    summary_text_file_url = serializers.SerializerMethodField()
    summary_text_file = serializers.FileField(write_only=True)

    class Meta:
        model = Summary
        fields = ['summary_text_file', 'summary_text_file_url', 'created_at', 'session']
        extra_kwargs = {'summary_text_file': {'write_only': True}}

    def get_summary_text_file_url(self, obj):
        return obj.get_summary_url()

    def validate_summary_text_file(self, value):
        if value.size > 1024 * 1024 * 5:  # Limiting file size to 5 MB
            raise serializers.ValidationError("File is too large ( > 5MB ).")
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(value.read(2048))
        if not mime_type.startswith('text'):
            raise serializers.ValidationError('This file is not a text file.')
        value.seek(0)
        return value


class TranscriptionSerializer(serializers.ModelSerializer):
    transcription_text_file_url = serializers.SerializerMethodField(read_only=True)
    transcription_text_file = serializers.FileField(write_only=True)

    class Meta:
        model = Transcription
        fields = ['transcription_text_file', 'transcription_text_file_url', 'created_at', 'session']
        extra_kwargs = {'transcription_text_file': {'write_only': True}}

    def get_transcription_text_file_url(self, obj):
        return obj.get_transcription_url()

    def validate_transcription_text_file(self, value):
        if value.size > 1024 * 1024 * 5:  # Limiting file size to 5 MB
            raise serializers.ValidationError("File is too large ( > 5MB ).")
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(value.read(2048))
        if not mime_type.startswith('text'):
            raise serializers.ValidationError('This file is not a text file.')
        value.seek(0)
        return value


class TherapistSessionSerializer(serializers.ModelSerializer):
    session_audio = serializers.FileField()
    session_audio_url = serializers.SerializerMethodField()
    errors = ErrorSerializer(many=True, read_only=True, source='errors_set')
    summaries = SummarySerializer(many=True, read_only=True, source='summaries_set')
    transcriptions = TranscriptionSerializer(many=True, read_only=True, source='transcriptions_set')

    class Meta:
        model = TherapistSession
        fields = ['id', 'session_name', 'session_audio', 'session_audio_url', 'errors', 'summaries', 'transcriptions', 'status']

    def get_session_audio_url(self, obj):
        return obj.get_session_audio_url()

    def validate_session_audio(self, value):
        # Existing validation logic
        if value.size > 1024 * 1024 * 50:
            raise serializers.ValidationError("Audio file is too large ( > 50MB ).")
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(value.read(2048))
        if not mime_type.startswith('audio'):
            raise serializers.ValidationError('This file is not an audio file.')
        value.seek(0)
        return value
