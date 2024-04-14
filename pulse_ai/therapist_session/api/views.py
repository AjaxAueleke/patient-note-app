from rest_framework import generics, permissions, mixins
from rest_framework.parsers import MultiPartParser, FormParser
from pulse_ai.therapist_session.models import TherapistSession
from .serializers import TherapistSessionSerializer
from .permissions import IsOwnerOrReadOnly

class TherapistSessionListView(generics.ListCreateAPIView):

    serializer_class = TherapistSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return TherapistSession.objects.filter(therapist=self.request.user)

    def perform_create(self, serializer):
        serializer.save(therapist=self.request.user)

class TherapistSessionDetailView(generics.RetrieveUpdateDestroyAPIView, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = TherapistSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return TherapistSession.objects.filter(therapist=self.request.user)

