from rest_framework import viewsets, filters

from pulse_ai.therapist_session.api.pagination import StandardResultsSetPagination
from .models import Patient
from .serializers import PatientSerializer

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'age']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # Additional filtering logic if needed
        return super().get_queryset()

