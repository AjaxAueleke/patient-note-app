import magic
from django.core.exceptions import ValidationError

def validate_audio_mime_type(value):
    mime = magic.Magic(mime=True)
    mime_type = mime.from_buffer(value.file.read(2048))  # Read the first few bytes to determine MIME type
    if not mime_type.startswith('audio'):
        raise ValidationError('This file is not an audio file.')
    value.file.seek(0)  # Reset file pointer after reading

