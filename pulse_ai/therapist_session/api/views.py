import json
import logging

import boto3
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework import status
from rest_framework import viewsets, permissions
from rest_framework.exceptions import APIException, ValidationError as DRFValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from pulse_ai.therapist_session.models import TherapistSession
from .permissions import IsOwnerOrReadOnly
from .serializers import TherapistSessionSerializer
from .serializers import TranscriptionSerializer, SummarySerializer, ErrorSerializer

logger = logging.getLogger(__name__)


class TherapistSessionViewSet(viewsets.ModelViewSet):
    serializer_class = TherapistSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        # This ensures that users only see their own sessions
        return TherapistSession.objects.filter(therapist=self.request.user)

    import logging

    # Configure logging
    logger = logging.getLogger(__name__)

    def perform_create(self, serializer):
        try:
            session = serializer.save(therapist=self.request.user)
            data = {"action": "speech-to-text", "audio_url": session.session_audio.url, "session_id": session.id}
            self._send_queue_message(data)
        except (ValidationError, IntegrityError) as e:
            logger.error(f"Database error during session creation: {e}")
            # Raise a DRF ValidationError which will be handled by DRF and turned into a 400 Bad Request
            raise DRFValidationError({"error": "Invalid data provided. Please check your inputs."})
        except Exception as e:
            logger.error(f"Unexpected error during session creation: {e}")
            print(e)
            raise APIException({"error": "An unexpected error occurred. Please try again later."})

    def _send_queue_message(self, data):
        queue_url = settings.SQS_URL

        sqs = boto3.client('sqs', aws_access_key_id=settings.FUNCTION_QUEUE_AWS_S3_AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.FUNCTION_QUEUE_AWS_S3_AWS_SECRET_ACCESS_KEY,
                           region_name=settings.AWS_REGION)
        # Send message
        response = sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(data),
                                    MessageGroupId='therapist-session-queue')

        print(response)


class SessionDataView(APIView):
    def post(self, request, session_id):
        session = TherapistSession.objects.filter(id=session_id).first()
        if not session:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        error = request.data.get('error', 'false').lower() == 'true'

        if error:
            error_serializer = ErrorSerializer(
                data={'session': session_id, 'error_message': request.data.get('error_message', ''),
                    'error_code': request.data.get('error_code', '')})
            if error_serializer.is_valid():
                error_serializer.save()
                return Response(error_serializer.data, status=status.HTTP_201_CREATED)
            return Response(error_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            transcription_data = {'session': session_id,
                'transcription_text_file': request.FILES.get('transcription_file')}
            summary_data = {'session': session_id, 'summary_text_file': request.FILES.get('summary_file')}
            transcription_serializer = TranscriptionSerializer(data=transcription_data)
            summary_serializer = SummarySerializer(data=summary_data)

            if transcription_serializer.is_valid() and summary_serializer.is_valid():
                transcription_serializer.save()
                summary_serializer.save()
                return Response({'transcription': transcription_serializer.data, 'summary': summary_serializer.data},
                    status=status.HTTP_201_CREATED)
            else:
                errors = {}
                if not transcription_serializer.is_valid():
                    errors['transcription'] = transcription_serializer.errors
                if not summary_serializer.is_valid():
                    errors['summary'] = summary_serializer.errors
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
