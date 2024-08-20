# from rest_framework import viewsets, permissions, status
# from rest_framework.exceptions import ValidationError
# from rest_framework.response import Response
# from .models import Favorite
# from .serializers import FavoriteSerializer
# from pulse_ai.therapist_session.models import TherapistSession
# from pulse_ai.therapist_session.api.permissions import IsOwnerOrReadOnly
# from pulse_ai.therapist_session.api.pagination import StandardResultsSetPagination

# class FavoriteViewSet(viewsets.ModelViewSet):
#     serializer_class = FavoriteSerializer
#     pagination_class = StandardResultsSetPagination
#     permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
#     http_method_names = ['get', 'post']  # Allow GET and POST methods

#     def get_queryset(self):
#         # Return only the favorites of the authenticated user
#         return Favorite.objects.filter(user=self.request.user)

#     def perform_create(self, serializer):
#         session = serializer.validated_data['session']
#         favorite = self.request.data.get('favorite', True)  # Default to true if not provided

#         # Check if the session belongs to the logged-in therapist
#         if session.therapist != self.request.user:
#             raise ValidationError("You can only favorite your own sessions.")

#         if favorite:
#             # Check if the favorite already exists
#             if Favorite.objects.filter(user=self.request.user, session=session).exists():
#                 raise ValidationError("This session is already in your favorites.")
#             # Create the favorite
#             serializer.save(user=self.request.user)
#             return Response({'status': 'Session favorited successfully.'}, status=status.HTTP_201_CREATED)

#         else:
#             # Check if the favorite exists
#             favorite_instance = Favorite.objects.filter(user=self.reque
# 
# st.user, session=session).first()
#             if not favorite_instance:
#                 raise ValidationError("This session is not in your favorites.")
#             # Delete the favorite
#             favorite_instance.delete()
#             return Response({'status': 'Session unfavorited successfully.'}, status=status.HTTP_204_NO_CONTENT)


from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import ValidationError, NotFound
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
    http_method_names = ['get', 'post']

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        try:
            session = serializer.validated_data['session']
            favorite = self.request.data.get('favorite', True)

            if session.therapist != self.request.user:
                raise ValidationError("You can only favorite your own sessions.")

            if favorite:
                if Favorite.objects.filter(user=self.request.user, session=session).exists():
                    raise ValidationError("This session is already in your favorites.")
                serializer.save(user=self.request.user)
                return Response({
                    'status': 'success',
                    'message': 'Session favorited successfully.',
                    'data': FavoriteSerializer(serializer.instance).data
                }, status=status.HTTP_201_CREATED)
            else:
                favorite_instance = Favorite.objects.filter(user=self.request.user, session=session).first()
                if not favorite_instance:
                    raise ValidationError("This session is not in your favorites.")
                favorite_instance.delete()
                return Response({
                    'status': 'success',
                    'message': 'Session unfavorited successfully.'
                }, status=status.HTTP_204_NO_CONTENT)

        except ValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e.detail[0]) if isinstance(e.detail, list) else str(e.detail)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'An unexpected error occurred.',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            return Response({
                'status': 'success',
                'data': response.data,
                'count': self.get_queryset().count()
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'An unexpected error occurred while fetching the list.',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        try:
            response = super().retrieve(request, *args, **kwargs)
            return Response({
                'status': 'success',
                'data': response.data
            }, status=status.HTTP_200_OK)
        except NotFound:
            return Response({
                'status': 'error',
                'message': 'Favorite not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'An unexpected error occurred while fetching the favorite.',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
