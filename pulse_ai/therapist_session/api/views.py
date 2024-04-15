from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from pulse_ai.therapist_session.models import TherapistSession
from .serializers import TherapistSessionSerializer
from .permissions import IsOwnerOrReadOnly

class TherapistSessionViewSet(viewsets.ModelViewSet):
    serializer_class = TherapistSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        # This ensures that users only see their own sessions
        return TherapistSession.objects.filter(therapist=self.request.user)

    def perform_create(self, serializer):
        serializer.save(therapist=self.request.user)
