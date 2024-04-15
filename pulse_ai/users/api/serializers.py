from django.contrib.auth import login
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework import exceptions
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer



from pulse_ai.users.models import User

class UserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["email", "last_login", "name", "password"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer class to register users.
    This is an organization level sign up.

    Meaning the user will be the owner of the organization.
    And the organization will have a default team upon signup.
    Users can be added to the team later.
    Users can be added to multiple teams later.
    """

    email = serializers.CharField()
    name = serializers.CharField()
    password = serializers.CharField()

    class Meta:
        model = User
        fields = ["email", "password", "name"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate_password(self, password):
        validate_password(password)
        return password

    def create(self, validated_data):
        try:
            # Create a CustomUser
            user = User.objects.create(
                email=validated_data["email"],
                name=validated_data["name"],
            )
            user.set_password(validated_data["password"])
            user.save()

            return user
        except Exception as e:
            return Response(
                data={f"Error in UserRegistrationSerializer - {e!s}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserLoginSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField(allow_blank=False, required=True)
    password = serializers.CharField(allow_blank=False, required=True)

    class Meta:
        model = User
        fields = ("email", "password")

    def validate(self, data):
        print(f"data in validate => {data}")
        try:
            user = User.objects.get(email=data["email"])
            print(f"user in validate UserLoginSerializer => {user}")
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User does not exist")
        return data

    def validate_email(self, value):
        """Emails are always stored and compared in lowercase."""
        return value.lower()

    @classmethod
    def get_token(cls, user):
        token = super(UserLoginSerializer, cls).get_token(user)
        print(f"token in get_token => {token}")

        # Add custom claims
        token["email"] = user.email

        return token

    @staticmethod
    def login(user, request):
        """
        Log-in user and append authentication token to serialized response.
        """
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        auth_token, token_created = Token.objects.get_or_create(user=user)
        print(f"auth_token in login => {auth_token}")
        serializer = UserSerializer(user, context={"request": request})
        response_data = serializer.data
        print(f"response_data in login => {response_data}")
        response_data["token"] = auth_token.key
        return response_data
