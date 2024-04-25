import json
import logging

import boto3
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework import viewsets, permissions
from rest_framework.exceptions import APIException, ValidationError as DRFValidationError
from rest_framework.parsers import MultiPartParser, FormParser

from pulse_ai.therapist_session.models import TherapistSession
from .permissions import IsOwnerOrReadOnly
from .serializers import TherapistSessionSerializer

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
