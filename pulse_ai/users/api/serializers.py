from django.contrib.auth import login
from django.contrib.auth.password_validation import validate_password
from django.core.files.images import get_image_dimensions
from django.db import IntegrityError
from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from pulse_ai.users.models import User


class ValidatedImageField(serializers.ImageField):
    def to_internal_value(self, data):
        # Call the superclass method that validates the uploaded file is an image
        file = super(ValidatedImageField, self).to_internal_value(data)

        # Check the image size
        max_upload_size = 5 * 1024 * 1024  # 5MB
        if file.size > max_upload_size:
            raise serializers.ValidationError("Image size should not exceed 5MB.")

        # Check the image resolution
        w, h = get_image_dimensions(file)
        max_width = max_height = 4096  # pixels
        if w > max_width or h > max_height:
            raise serializers.ValidationError("Image dimensions should not exceed 2048x2048 pixels.")

        # Check image type (optional)
        if file.image.format.lower() not in ['jpeg', 'jpg', 'png']:
            raise serializers.ValidationError("Image format not supported. Use JPEG or PNG.")

        return file


class UserSerializer(serializers.ModelSerializer[User]):
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["email", "last_login", "name", "profile_picture_url"]

    def get_profile_picture_url(self, obj):
        return obj.get_profile_picture_url()


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.CharField()
    name = serializers.CharField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "name"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, value):
        """
        Check if a user with this email already exists.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate_password(self, password):
        validate_password(password)
        return password

    def create(self, validated_data):
        """
        Create a new user instance. If there is an issue during the creation,
        the error is propagated by raising an IntegrityError.
        """
        try:
            user = User.objects.create(email=validated_data["email"], name=validated_data["name"])
            user.set_password(validated_data["password"])
            user.save()
            return user
        except IntegrityError as e:
            raise IntegrityError(f"Error creating user: {e}")


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


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate_new_password(self, value):
        user = self.context['request'].user
        validate_password(value, user)
        return value


class UserProfilePictureSerializer(serializers.ModelSerializer):
    profile_picture = ValidatedImageField()

    class Meta:
        model = User
        fields = ['profile_picture']

    def save(self, **kwargs):
        user = self.context['request'].user
        user.profile_picture = self.validated_data.get('profile_picture', user.profile_picture)
        user.save()
        return user
