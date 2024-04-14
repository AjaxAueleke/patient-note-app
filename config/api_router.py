from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from pulse_ai.users.api.views import UserViewSet
from pulse_ai.therapist_session.api.views import TherapistSessionListView

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)
router.register("therapists", TherapistSessionListView)


app_name = "api"
urlpatterns = router.urls
