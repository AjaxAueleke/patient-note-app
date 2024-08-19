from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .models import Favorite
from .serializers import FavoriteSerializer
from pulse_ai.therapist_session.models import TherapistSession
from pulse_ai.therapist_session.api.permissions import IsOwnerOrReadOnly
from pulse_ai.therapist_session.api.pagination import StandardResultsSetPagination

class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    http_method_names = ['get', 'post']  # Allow GET and POST methods

    def get_queryset(self):
        # Return only the favorites of the authenticated user
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        session = serializer.validated_data['session']
        favorite = self.request.data.get('favorite', True)  # Default to true if not provided

        # Check if the session belongs to the logged-in therapist
        if session.therapist != self.request.user:
            raise ValidationError("You can only favorite your own sessions.")

        if favorite:
            # Check if the favorite already exists
            if Favorite.objects.filter(user=self.request.user, session=session).exists():
                raise ValidationError("This session is already in your favorites.")
            # Create the favorite
            serializer.save(user=self.request.user)
            return Response({'status': 'Session favorited successfully.'}, status=status.HTTP_201_CREATED)

        else:
            # Check if the favorite exists
            favorite_instance = Favorite.objects.filter(user=self.request.user, session=session).first()
            if not favorite_instance:
                raise ValidationError("This session is not in your favorites.")
            # Delete the favorite
            favorite_instance.delete()
            return Response({'status': 'Session unfavorited successfully.'}, status=status.HTTP_204_NO_CONTENT)
