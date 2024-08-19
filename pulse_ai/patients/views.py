from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated  # Ensure the user is authenticated
from .models import Patient
from .serializers import PatientSerializer
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
        # Additional filtering logic if needed
        return super().get_queryset()

    def perform_create(self, serializer):
        # Automatically set the therapist to the logged-in user
        serializer.save(therapist=self.request.user)
