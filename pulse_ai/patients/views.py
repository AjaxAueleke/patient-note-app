# from rest_framework import viewsets, filters, status
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.exceptions import ValidationError, NotFound
# from .models import Patient
# from .serializers import PatientSerializer
# from pulse_ai.therapist_session.api.pagination import StandardResultsSetPagination

# class PatientViewSet(viewsets.ModelViewSet):
#     queryset = Patient.objects.all()
#     serializer_class = PatientSerializer
#     filter_backends = [filters.SearchFilter, filters.OrderingFilter]
#     search_fields = ['name']
#     ordering_fields = ['name', 'age']
#     pagination_class = StandardResultsSetPagination
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return super().get_queryset()

#     def perform_create(self, serializer):
#         try:
#             serializer.save(therapist=self.request.user)
#             return Response({
#                 'status': 'success',
#                 'message': 'Patient created successfully.',
#                 'data': PatientSerializer(serializer.instance).data
#             }, status=status.HTTP_201_CREATED)
#         except ValidationError as e:
#             return Response({
#                 'status': 'error',
#                 'message': str(e.detail[0]) if isinstance(e.detail, list) else str(e.detail)
#             }, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({
#                 'status': 'error',
#                 'message': 'An unexpected error occurred.',
#                 'detail': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def list(self, request, *args, **kwargs):
#         try:
#             response = super().list(request, *args, **kwargs)
#             return Response({
#                 'status': 'success',
#                 'data': response.data,
#                 'count': self.get_queryset().count()
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({
#                 'status': 'error',
#                 'message': 'An unexpected error occurred while fetching the list.',
#                 'detail': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def retrieve(self, request, *args, **kwargs):
#         try:
#             response = super().retrieve(request, *args, **kwargs)
#             return Response({
#                 'status': 'success',
#                 'data': response.data
#             }, status=status.HTTP_200_OK)
#         except NotFound:
#             return Response({
#                 'status': 'error',
#                 'message': 'Patient not found.'
#             }, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({
#                 'status': 'error',
#                 'message': 'An unexpected error occurred while fetching the patient.',
#                 'detail': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.decorators import action
from .models import Patient
from .serializers import PatientSerializer
from pulse_ai.therapist_session.api.serializers import TherapistSessionSerializer
from pulse_ai.therapist_session.models import TherapistSession
from pulse_ai.therapist_session.api.pagination import StandardResultsSetPagination

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'age']
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset()

    def perform_create(self, serializer):
        try:
            serializer.save(therapist=self.request.user)
            return Response({
                'status': 'success',
                'message': 'Patient created successfully.',
                'data': PatientSerializer(serializer.instance).data
            }, status=status.HTTP_201_CREATED)
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
                'message': 'Patient not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'An unexpected error occurred while fetching the patient.',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='details')
    def get_patient_details_with_sessions(self, request, pk=None):
        try:
            # Fetch the patient by ID
            patient = self.get_object()

            # Fetch all therapist sessions associated with this patient
            therapist_sessions = TherapistSession.objects.filter(patient=patient)

            # Serialize the data
            patient_data = PatientSerializer(patient).data
            sessions_data = TherapistSessionSerializer(therapist_sessions, many=True).data

            # Combine the data into a structured response
            response_data = {
                'patient': patient_data,
                'therapist_sessions': sessions_data
            }

            return Response({
                'status': 'success',
                'data': response_data
            }, status=status.HTTP_200_OK)

        except Patient.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Patient not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'An unexpected error occurred.',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
