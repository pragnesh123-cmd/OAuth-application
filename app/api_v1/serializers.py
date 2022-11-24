from app.models import User
from rest_framework import serializers
from django.contrib.auth.models import Permission, Group
from rest_framework.validators import ValidationError
from rest_framework.authtoken.models import Token


class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ("id","name",)


class PermissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Permission
        fields = "__all__"


class SignUpSerializer(serializers.ModelSerializer):
    email = serializers.CharField(max_length=80)
    username = serializers.CharField(max_length=45)
    password = serializers.CharField(min_length=8, write_only=True)

    class Meta:
        model = User
        fields = ["email", "username", "password"]
    
    def validate(self, attrs):
        if email_exists := User.objects.filter(email=attrs["email"]).exists():
            raise ValidationError("Email has already been used")
        return super().validate(attrs)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        # Token.objects.create(user=user)
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    """
    Serializer for password forgot endpoint.
    """

    email = serializers.EmailField()

    def is_valid(self, raise_exception=False):
        email = self.initial_data.get("email")
        if email is None or len(email.strip())==0:
            raise ValidationError("The email field may not be blank.")
        try:
            user = User.objects.get(email__iexact=email)
            self.__class__.user = user
        except User.DoesNotExist as e:
            raise ValidationError("This email has not been registered.")
        return email

class PasswordVerifySerializer(serializers.Serializer):
    """
    Serializer for forgot password verify endpoint.
    """

    password1 = serializers.CharField(
        label="Password1",
    )
    password2 = serializers.CharField(
        label="Password2",
    )

    def validate(self, attrs):
        if attrs["password1"] != attrs["password2"]:
            raise ValidationError("The password does not match.")

        return attrs