import os
import requests 
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from .models import User
from .serializers import RegisterSerializer, UserSerializer

# =========================
# Custom JWT Serializer
# =========================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        if user.is_blocked:
            raise AuthenticationFailed("Your account has been blocked")
        
        if not user.is_active:
            raise AuthenticationFailed("This account is inactive")

        # Standardized Response using UserSerializer
        data["user"] = UserSerializer(user).data

        return data


# =========================
# Register API
# =========================
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "User registered successfully"},
            status=status.HTTP_201_CREATED
        )


# =========================
# Login API (JWT)
# =========================
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


# =========================
# User Profile API
# =========================
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# =========================
# Logout API
# =========================
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                raise AuthenticationFailed("Refresh token is required")

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Logged out successfully"},
                status=status.HTTP_200_OK
            )
        except Exception:
            raise AuthenticationFailed("Invalid or expired token")


# =========================
# Google Auth API
# =========================
class GoogleAuthView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        data = request.data
        token = data.get("token") or data.get("access_token") or data.get("credential")

        if not token:
            return Response({"error": "Token missing"}, status=status.HTTP_400_BAD_REQUEST)

# Replace the hardcoded string with os.getenv
        user_info_url = os.getenv('GOOGLE_USER_INFO_URL')

# Now the request uses the URL from the .env file
        response = requests.get(user_info_url, params={"access_token": token})

        if not response.ok:
            return Response(
                {"error": "Failed to validate token with Google", "details": response.json()},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_data = response.json()
        email = user_data.get("email")
        first_name = user_data.get("given_name", "")
        last_name = user_data.get("family_name", "")
        
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True
            }
        )
        
        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data
        })

