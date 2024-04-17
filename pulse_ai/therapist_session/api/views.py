import json

import boto3
from django.conf import settings
from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser

from pulse_ai.therapist_session.models import TherapistSession
from .permissions import IsOwnerOrReadOnly
from .serializers import TherapistSessionSerializer


class TherapistSessionViewSet(viewsets.ModelViewSet):
    serializer_class = TherapistSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        # This ensures that users only see their own sessions
        return TherapistSession.objects.filter(therapist=self.request.user)

    def perform_create(self, serializer):
        session = serializer.save(therapist=self.request.user)
        data = {"action": "speech-to-text", "audio_url": session.session_audio.url, "session_id": session.id}
        self._send_queue_message(data)

    def _send_queue_message(self, data):
        queue_url = settings.SQS_URL

        sqs = boto3.client('sqs', region_name=settings.AWS_REGION)
        # Send message
        response = sqs.send_message(QueueUrl=queue_url, DelaySeconds=10, MessageBody=json.dumps(data))
        print(response)
