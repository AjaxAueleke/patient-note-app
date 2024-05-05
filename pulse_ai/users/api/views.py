from random import randint

from django.conf import settings
from django.contrib.auth import authenticate, update_session_auth_hash
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin, DestroyModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from sendgrid import SendGridAPIClient, Email
from sendgrid.helpers.mail import Mail, Content

from pulse_ai.users.api.permissions import IsNotDeleted
from pulse_ai.users.api.serializers import UserRegistrationSerializer, UserLoginSerializer, ChangePasswordSerializer, \
    UserProfilePictureSerializer, EmailVerificationSerializer, UserSerializer, VerifyEmailSerializer
from pulse_ai.users.models import User
from pulse_ai.users.throttles import BurstRateThrottle, SustainedRateThrottle


class UserViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "pk"
    permission_classes = [IsAuthenticated, IsNotDeleted]  # Ensures that the user is authenticated

    def get_queryset(self, *args, **kwargs):
        # Ensure that the user can only access their own data
        assert isinstance(self.request.user.id, int)
        return self.queryset.filter(id=self.request.user.id)

    def destroy(self, request, *args):
        # Get the user from the request (i.e., the logged-in user)
        user = request.user
        user.delete()
        return Response({"success": True, "message": "User account has been successfully deleted."},
                        status=status.HTTP_200_OK)


    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class ChangePasswordView(APIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated, IsNotDeleted]

    def patch(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            update_session_auth_hash(request, user)  # Important to keep the session active
            return Response({"success": True, "message": "Password changed"}, status=status.HTTP_200_OK)
        else:
            return Response({"success": False, "message": "Error changing password", "errors": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = ()

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "User registered successfully", "data": serializer.data},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"success": False, "message": "Error creating a user", "errors": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == "POST":
            return UserRegistrationSerializer


class UserLoginView(TokenObtainPairView):
    """
    An endpoint to authenticate existing users using their email and password.
    """

    serializer_class = UserLoginSerializer
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        """
        Validate user credentials, login, and return serialized user + auth token.
        """

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(**serializer.validated_data)
        if user is None:
            return Response(
                data={"success": False, "message": "Incorrect email and password combination. Please try again.", },
                status=status.HTTP_400_BAD_REQUEST, )

        response_data = UserLoginSerializer.login(user, request)
        token = RefreshToken.for_user(user)
        response_data["refresh"] = str(token)
        response_data["access"] = str(token.access_token)
        response_data["success"] = True
        return Response(response_data, status=status.HTTP_202_ACCEPTED)


class UpdateProfilePictureView(APIView):
    permission_classes = [IsAuthenticated, IsNotDeleted,]
    parser_classes = [MultiPartParser, FormParser]


    def patch(self, request, *args, **kwargs):
        serializer = UserProfilePictureSerializer(instance=request.user, data=request.data,
                                                  context={'request': request}, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            profile_picture_url = user.get_profile_picture_url()
            return Response({"success": True, "message": "Profile picture updated",
                             "data": {"profile_picture_url": profile_picture_url}},

                            status=status.HTTP_200_OK)
        else:
            return Response(
                {"success": False, "message": "Failed to update profile picture", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST)



class SendVerificationEmailView(APIView):
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
    serializer_class = EmailVerificationSerializer
    permission_classes = (IsAuthenticated, IsNotDeleted)

    def post(self, request, *args, **kwargs):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = request.user
            verification_code = "".join([str(randint(0, 9)) for _ in range(6)])  # Generate a 6-digit code
            user.verification_code = verification_code
            from_email = Email("ahmed.jamil7410@gmail.com")
            to_email = Email(email)
            subject = 'Verify Your Email Address'
            message = f'Your verification code is: {verification_code}'
            content = Content("text/plain", message)

            try:
                sg = SendGridAPIClient(apikey=settings.SENDGRID_API_KEY)
                mail_message = Mail(from_email, subject, to_email, content)
                response = sg.client.mail.send.post(request_body=mail_message.get())
                print(response.status_code)
                print(response.body)
                print(response.headers)
                user.code_sent_at = timezone.now()
                user.save()
            except Exception as e:
                print(e)
                return Response({"success": False, "message": "There was an issue sending the verification email",
                                 "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"success": True, "message": "Verification email sent successfully."},
                            status=status.HTTP_200_OK)
        else:
            return Response({"success": False, "message": "There was an issue sending the verification email",
                             "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    permission_classes = (IsAuthenticated, IsNotDeleted)
    serializer_class = VerifyEmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = VerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            user.email_verified = True
            user.verification_code = None
            user.save()
            return Response({"success": True, "message": "Email verified successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
