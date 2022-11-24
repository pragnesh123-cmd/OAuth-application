from django.contrib import admin
from django.urls import re_path
from rest_framework import routers
from app.api_v1 import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

app_name = "app"

router = routers.SimpleRouter()
router.register("roles", views.RoleViewset)
router.register("permissions", views.PermissionsViewset)

urlpatterns = [
    re_path(r"admin/", admin.site.urls),
    re_path(r"set-role-permissions/$", views.SetRoleAndPermissionsApiView.as_view()),
    re_path(
        r"set-user-role-permissions/$", views.SetUserRoleAndPermissionsApiView.as_view()
    ),
    re_path(r"signup/$", views.SignUpView.as_view(), name="signup"),
    re_path(r"login/$", views.LoginWithOTPView.as_view(), name="login"),
    re_path(r"change-password/$", views.ChangePasswordAPIView.as_view()),
    re_path(r"forgot-password/$", views.ForgotPasswordAPIView.as_view()),
    re_path(
        r"forgot-password-token-verify/$",
        views.ForgotPasswordTokenVerifyAPIView.as_view(),
    ),
    re_path(
        r"forgot-password-confirm/$",
        views.ForgotPasswordConfirmView.as_view(),
    ),
    re_path(r"jwt/create/$", TokenObtainPairView.as_view(), name="jwt_create"),
    re_path(r"jwt/refresh/$", TokenRefreshView.as_view(), name="token_refresh"),
    re_path(r"jwt/verify/$", TokenVerifyView.as_view(), name="token_verify"),
] + router.urls
