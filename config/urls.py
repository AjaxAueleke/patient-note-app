# ruff: noqa
from django.conf import settings
from django.urls import include
from django.urls import path
from django.views import defaults as default_views
from drf_spectacular.views import SpectacularAPIView
from drf_spectacular.views import SpectacularSwaggerView

from pulse_ai.therapist_session.api.views import SessionDataView
from pulse_ai.users.api.views import UserLoginView, RegisterView, ChangePasswordView, UpdateProfilePictureView, \
    SendVerificationEmailView

urlpatterns = []

# API URLS
urlpatterns += [
    path("api/", include("config.api_router")),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("users/register", RegisterView.as_view()), path("users/login", UserLoginView.as_view()),
    path("users/password", ChangePasswordView.as_view()), path("users/picture", UpdateProfilePictureView.as_view()),
    path("users/send-verification-email", SendVerificationEmailView.as_view(), name='send-verification-email'),
    path("users/verify-email", SendVerificationEmailView.as_view(), name='verify-email'),
    path("session-data/<int:session_id>/", SessionDataView.as_view(), name="session-data"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs", ),
]

if settings.DEBUG:
    urlpatterns += [path("400/", default_views.bad_request, kwargs={"exception": Exception("Bad Request!")}, ),
                    path("403/", default_views.permission_denied,
                         kwargs={"exception": Exception("Permission Denied")}, ),
                    path("404/", default_views.page_not_found, kwargs={"exception": Exception("Page not Found")}, ),
                    path("500/", default_views.server_error), ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
