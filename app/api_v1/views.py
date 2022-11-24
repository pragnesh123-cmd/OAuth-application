from app.permissions import CheckPermission
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth.models import Permission, Group
from app.models import  User, ForgotPasswordToken
from app.token import create_jwt_pair_for_user
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password,check_password
from app.custom_token_generator import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from app.api_v1.serializers import ForgotPasswordSerializer, PasswordVerifySerializer,SignUpSerializer,PermissionSerializer, RoleSerializer
from django.utils.encoding import force_bytes
from T1 import settings
from app.sendgrid import SendGrid
import random
from app.mailjet import send_forgot_passwork_link_to_mail, send_otp_to_mail

class RoleViewset(ModelViewSet):
    """
    :An endpoint for get all roles and create new role.
    """
    queryset = Group.objects.all()
    serializer_class = RoleSerializer
    permission_classes = []

    def get_queryset(self):
        queryset = super(RoleViewset, self).get_queryset()
        queryset = Group.objects.all()
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)


class PermissionsViewset(ModelViewSet):
    """
    :An endpoint for get all permissions
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = []

    def get_queryset(self):
        return super(PermissionsViewset, self).get_queryset()


class SetRoleAndPermissionsApiView(generics.CreateAPIView):
    """
    :An endpoint for asign permissions to role.
    """
    permission_classes = []

    def post(self, request, *args, **kwargs):
        role = self.request.data.get("role")
        permissions = self.request.data.get("permissions")
        group = Group.objects.get(id=role)
        group.permissions.set(permissions)
        return Response(status=status.HTTP_201_CREATED)


class SetUserRoleAndPermissionsApiView(generics.CreateAPIView):
    """
    :An endpoint for asign role for user.
    """
    permission_classes = []

    def post(self, request, *args, **kwargs):
        user_id = self.request.data.get("user_id")
        role_id = self.request.data.get("role_id")
        user = User.objects.get(id=user_id)
        user.groups.set([role_id])
        return Response(status=status.HTTP_201_CREATED)


class SignUpView(generics.GenericAPIView):
    """
    :An endpoint for registration.
    """
    serializer_class = SignUpSerializer
    permission_classes = []

    def post(self, request):
        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            response = {"error":False,"message": "User Created Successfully", "data": serializer.data}
            return Response(data=response, status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginWithOTPView(APIView):
    """
    :An endpoint for login.
    """
    permission_classes = []

    def get(self, request):
        email = request.query_params.get("email")
        if not User.objects.filter(email=email).exists():
            return Response(data={"message": "email is not registered"})
        otp = random.randint(100000, 999999)
        """
        please sendgrid try except block comment then api call beacaue my sendgrid account is under review so i not added API_KEY in env file 
        """
        try:
            # SendGrid().send_otp_to_email(
            #     email,otp
            # )
            send_otp_to_mail(email,otp)
        except Exception as e:
            return Response(
            data={"error": True,"data":[],"message": "The otp is not sent successfully in mail because of some error in sendgrid."},
            status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        response = Response()
        response.data = {"message": "Otp send successfully"}
        # cookie expire time is 5 minutes
        response.set_cookie('otp', f'{otp}',max_age=300)
        response.set_cookie('email', f'{email}',max_age=300)
        return response

    def post(self,request):
        user_otp, user_email = request.data.get("otp"), request.data.get("email")
        otp ,email = request.COOKIES.get('otp'), request.COOKIES.get('email')
        if user_otp == otp and user_email == email:
            user = User.objects.filter(email=email).first()
            tokens = create_jwt_pair_for_user(user)
            return Response(data={"message": "Login successfully.","tokens":tokens})
        else:
            return Response(data={"message": "Otp is not validated or expired."})


class ChangePasswordAPIView(APIView):
    """
    :An endpoint for reset password.
    """
    permission_classes = [CheckPermission,]
    queryset = User.objects.all() 

    def put(self, request, *args, **kwargs):
        new_password = request.data.get("new_password")
        old_password = request.data.get("old_password")
        if check_password(old_password,request.user.password):
            User.objects.filter(email=request.user.email).update(
                password=make_password(new_password)
            )
            return Response(
                data={"error": False,"data":[],"message": "Successfully updated password."}, status=status.HTTP_200_OK
            )    
        return Response(
                data={"error": True,"data":[],"message": "old password doesn't match."}, status=status.HTTP_200_OK
            )


class ForgotPasswordAPIView(APIView):
    """
    :An endpoint for forgot password.
    """

    serializer_class = ForgotPasswordSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        useridb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        self.set_token(user, token)
        forgot_password_link = f"{settings.FRONTEND_FORGOT_PASSWORD_URL}?useridb64={useridb64}&token={token}"
        
        try:
            # SendGrid().send_email_to_forgot_password_link(
            #     email=user.email,
            #     username=user.get_full_name(),
            #     forgot_password_link=forgot_password_link,
            # )
            send_forgot_passwork_link_to_mail(user.email,user.get_full_name(),forgot_password_link)
            return Response(
                data={"error": False,"data":[],"message": "Forgotten password link has been successfully sent in email."},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
            data={"error": True,"data":[],"message": "The forgot password link is not sent successfully in mail because of some error in sendgrid."},
            status=status.HTTP_406_NOT_ACCEPTABLE,
            )
            
    def set_token(self, user, token):
        ForgotPasswordToken.objects.filter(user=user).update(is_active=False)
        ForgotPasswordToken.objects.create(user=user, token=token)


class ForgotPasswordTokenVerifyAPIView(APIView):
    """
    :An endpoint for forgot password token verifications
    """

    permission_classes = (AllowAny,)

    def get(self, request, *arg, **kwargs):
        useridb64 = request.GET.get("useridb64")
        token = request.GET.get("token")
        if (token is None or len(token)==0) and (useridb64 is None or len(useridb64)==0):
            return Response(
            data={"error": True,"data":[{"is_token_valid": False}],"message": "The token and useridb64 are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
        if useridb64 is None or len(useridb64)==0:
            return Response(
            data={"error": True,"data":[{"is_token_valid": False}],"message": "The useridb64 is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
        if token is None or len(token)==0:
            return Response(
            data={"error": True,"data":[{"is_token_valid": False}],"message": "The token is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
        try:
            uid = urlsafe_base64_decode(useridb64)
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if (
            user is not None
            and default_token_generator.check_token(user, token)
            and ForgotPasswordToken.objects.filter(
                user=user, token=token, is_active=True
            ).exists()
        ):
            return Response(
                data={"error": False,"data":[{"is_token_valid": True}],"message": "The token is validated."},
                status=status.HTTP_200_OK,
            )
        return Response(
            data={"error": True,"data":[{"is_token_valid": False}],"message": "The token is not validated."},
            status=status.HTTP_406_NOT_ACCEPTABLE,
        )



class ForgotPasswordConfirmView(APIView):
    """
    :An endpoint for forgot password confirmation
    """

    serializer_class = PasswordVerifySerializer
    permission_classes = (AllowAny,)

    def post(self, request, *arg, **kwargs):
        serializer = PasswordVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        useridb64 = request.data.get("useridb64")
        token = request.data.get("token")
        if (token is None or len(token)==0) and (useridb64 is None or len(useridb64)==0):
            return Response(
            data={"error": True,"data":[],"message": "The token and useridb64 are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
        if useridb64 is None or len(useridb64)==0:
            return Response(
            data={"error": True,"data":[],"message": "The useridb64 is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
        if token is None or len(token)==0:
            return Response(
            data={"error": True,"data":[],"message": "The token is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
        try:
            uid = urlsafe_base64_decode(useridb64)
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if (
            user is not None
            and default_token_generator.check_token(user, token)
            and ForgotPasswordToken.objects.filter(
                user=user, is_active=True, token=token
            ).exists()
        ):

            user.set_password(
                serializer.validated_data["password1"]
            )  # set_password also hashes the password that the user will get
            user.save()
            ForgotPasswordToken.objects.filter(user=user).update(is_active=False)
            return Response(
                data={"error": False,"data":[] ,"message": "Your password has been successfully set."},
                status=status.HTTP_200_OK,
            )
        return Response(
            data={
                "error": True,
                "data":[],
                "message": "The password reset link was invalid, possibly because it has already been used or expire. Please request a new password forgot.",
            },
            status=status.HTTP_406_NOT_ACCEPTABLE,
        )