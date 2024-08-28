import magic
from rest_framework import serializers
from patients.serializers import PatientSerializer
from pulse_ai import patients
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
        if value.size > 1024 * 1024 * 2:  # Limiting file size to 2 MB
            raise serializers.ValidationError("File is too large ( > 2MB ).")
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
        if value.size > 1024 * 1024 * 2:
            raise serializers.ValidationError("File is too large ( > 2MB ).")
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(value.read(2048))
        if not mime_type.startswith('text'):
            raise serializers.ValidationError('This file is not a text file.')
        value.seek(0)
        return value


# class TherapistSessionSerializer(serializers.ModelSerializer):
#     session_audio = serializers.FileField()
#     session_audio_url = serializers.SerializerMethodField()
#     errors = ErrorSerializer(many=True, read_only=True)
#     summaries = SummarySerializer(many=True, read_only=True)
#     transcriptions = TranscriptionSerializer(many=True, read_only=True)
#     patient = PatientSerializer(read_only=True)  # Use PatientSerializer instead of PrimaryKeyRelatedField
#     patient_id = serializers.IntegerField(write_only=True)
#     favorite = serializers.BooleanField(required=False,default=False)


#     class Meta:
#         model = TherapistSession
#         fields = [
#             'id',
#             'created_at',
#             'session_name',
#             'description',
#             'session_audio',
#             'session_audio_url',
#             'errors',
#             'summaries',
#             'transcriptions',
#             'status',
#             'patient',
#             'patient_id',
#             'favorite'
#         ]

#     def get_session_audio_url(self, obj):
#         return obj.get_session_audio_url()

#     def validate_session_audio(self, value):
#         # Existing validation logic
#         if value.size > 1024 * 1024 * 50:
#             raise serializers.ValidationError("Audio file is too large ( > 50MB ).")
#         # mime = magic.Magic(mime=True)
#         # mime_type = mime.from_buffer(value.read(2048))
#         # print("MIME TYPE:", mime_type)

#         # if not mime_type.startswith('audio'):
#         #     raise serializers.ValidationError('This file is not an audio file.')
#         # value.seek(0)
#         return value
class TherapistSessionSerializer(serializers.ModelSerializer):
    session_audio = serializers.FileField(write_only=True)
    session_audio_url = serializers.SerializerMethodField(read_only=True)
    errors = ErrorSerializer(many=True, read_only=True)
    summaries = SummarySerializer(many=True, read_only=True)
    transcriptions = TranscriptionSerializer(many=True, read_only=True)
    patient = PatientSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    favorite = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = TherapistSession
        fields = [
            'id',
            'created_at',
            'session_name',
            'description',
            'session_audio',
            'session_audio_url',
            'errors',
            'summaries',
            'transcriptions',
            'status',
            'patient',
            'patient_id',
            'favorite',
        ]

    def get_session_audio_url(self, obj):
        return obj.get_session_audio_url()

    def validate_session_audio(self, value):
        if isinstance(value, dict):
            # Assuming the `uri` is a base64 encoded string
            file_data = value.get('uri')
            file_type = value.get('type')  # File type will be handled generically
            file_name = value.get('name', 'uploaded_audio')

            if not file_data:
                raise serializers.ValidationError("File data is missing.")

            # Convert base64 to bytes
            try:
                # Removing the data URI prefix if it exists
                if file_data.startswith('data:'):
                    file_data = file_data.split(',')[1]
                decoded_file = base64.b64decode(file_data)
                # Preserve the original file extension
                file_name_with_extension = f"{file_name}.{file_type.split('/')[-1]}"
                file = ContentFile(decoded_file, name=file_name_with_extension)
            except TypeError:
                raise serializers.ValidationError("Invalid file format.")

            # Now `file` is a Django `ContentFile` object
            value = file
        
        # Ensure the file is below the size limit
        if value.size > 1024 * 1024 * 50:
            raise serializers.ValidationError("Audio file is too large ( > 50MB ).")

        # Optionally validate the MIME type
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(value.read(2048))
        if not mime_type.startswith('audio'):
            raise serializers.ValidationError('This file is not an audio file.')
        value.seek(0)  # Reset the file pointer after reading
        
        return value