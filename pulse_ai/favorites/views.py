from rest_framework import viewsets, permissions
from .models import Favorite
from .serializers import FavoriteSerializer
from pulse_ai.therapist_session.api.permissions import IsOwnerOrReadOnly

class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # Return only the favorites of the authenticated user
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign the current user to the favorite
        serializer.save(user=self.request.user)