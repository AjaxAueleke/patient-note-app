from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from pulse_ai.users.api.views import UserViewSet
from pulse_ai.therapist_session.api.views import RegenerateSummaryViewSet, RegenerateTranscriptionViewSet, TherapistSessionViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet, basename="user")
router.register(r'therapist_session', TherapistSessionViewSet, basename="therapist")
router.register(r'therapist_session/(?P<session_id>\d+)/regenerate-transcription', RegenerateTranscriptionViewSet, basename='regenerate-transcription')
router.register(r'therapist_session/(?P<session_id>\d+)/regenerate-summary', RegenerateSummaryViewSet, basename='regenerate-summary')

app_name = "api"
urlpatterns = router.urls
