import os
import requests 
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

# Firebase Imports
from firebase_admin import auth as firebase_auth

# Import Serializers
from .serializers import (
    RegisterSerializer, 
    UserSerializer, 
    AdminUserSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)

# Import Utils for OTP Email
from .utils import send_otp_email

# Try Importing Models (In case apps aren't ready yet)
try:
    from products.models import Product
except ImportError:
    Product = None

try:
    from orders.models import Order
except ImportError:
    Order = None

User = get_user_model()

# ==========================================
# 1. Standard Login (Email/Password)
# ==========================================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # 1. Authenticate (checks email/password)
        try:
            data = super().validate(attrs)
        except AuthenticationFailed:
            raise AuthenticationFailed("Invalid credentials or inactive account.")

        # 2. STRICT BLOCK CHECK
        if hasattr(self.user, 'is_blocked') and self.user.is_blocked:
            raise AuthenticationFailed("Your account has been blocked by the administrator.")
        
        if not self.user.is_active:
            raise AuthenticationFailed("This account is inactive.")

        # 3. Add User Data to Response
        user_data = UserSerializer(self.user).data
        user_data['is_staff'] = self.user.is_staff
        user_data['is_superuser'] = self.user.is_superuser
        data["user"] = user_data

        return data

class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


# ==========================================
# 2. Google Login
# ==========================================
class GoogleAuthView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        data = request.data
        token = data.get("token") or data.get("access_token") or data.get("credential")

        if not token:
            return Response({"error": "Token missing"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate with Google
        user_info_url = os.getenv('GOOGLE_USER_INFO_URL', "https://www.googleapis.com/oauth2/v3/userinfo")
        response = requests.get(user_info_url, params={"access_token": token})

        if not response.ok:
            return Response(
                {"error": "Failed to validate token with Google", "details": response.json()},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_data_google = response.json()
        email = user_data_google.get("email")
        
        # Get or Create User
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": user_data_google.get("given_name", ""),
                "last_name": user_data_google.get("family_name", ""),
                "is_active": True
            }
        )

        # STOP LOGIN IF BLOCKED
        if user.is_blocked or not user.is_active:
            return Response(
                {"error": "Your account has been blocked by the administrator."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate Token
        refresh = RefreshToken.for_user(user)
        serialized_user = UserSerializer(user).data
        serialized_user['is_staff'] = user.is_staff
        serialized_user['is_superuser'] = user.is_superuser

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": serialized_user
        })


# ==========================================
# 3. Firebase Phone Login
# ==========================================
class FirebasePhoneAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get('id_token')
        if not id_token:
            return Response({'error': 'No token provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validate with Firebase
            decoded_token = firebase_auth.verify_id_token(id_token)
            phone_number = decoded_token.get('phone_number')

            if not phone_number:
                return Response({'error': 'Invalid Token: No phone number found'}, status=status.HTTP_400_BAD_REQUEST)

            user, created = User.objects.get_or_create(
                phone_number=phone_number,
                defaults={
                    'email': f"{phone_number.strip('+')}@mobile.login", 
                    'first_name': 'Mobile',
                    'last_name': 'User',
                    'is_active': True
                }
            )

            # STOP LOGIN IF BLOCKED
            if user.is_blocked or not user.is_active:
                return Response(
                    {"error": "Your account has been blocked by the administrator."}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Generate Token
            refresh = RefreshToken.for_user(user)
            serialized_user = UserSerializer(user).data
            serialized_user['is_staff'] = user.is_staff
            serialized_user['is_superuser'] = user.is_superuser
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': serialized_user
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# 4. Register API
# ==========================================
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


# ==========================================
# 5. User Profile (Runs on Refresh)
# ==========================================
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Double check logic for users who are already logged in but get blocked
        if hasattr(request.user, 'is_blocked') and request.user.is_blocked:
             return Response(
                 {"detail": "Your account has been blocked."}, 
                 status=status.HTTP_403_FORBIDDEN
             )
             
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# ==========================================
# 6. Logout API
# ==========================================
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                raise AuthenticationFailed("Refresh token is required")

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        except Exception:
            raise AuthenticationFailed("Invalid or expired token")


# ==========================================
# 7. Password Reset (OTP Method) - CORRECTED
# ==========================================
class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = request.data['email']
            
            # SILENT CHECK: Only send OTP if user exists in DB
            # This prevents 400 errors for non-existent users (High UX/Security)
            if User.objects.filter(email=email).exists():
                send_otp_email(email)
            
            # Always return 200 OK
            return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)


# ==========================================
# 8. Admin Dashboard Stats
# ==========================================
class AdminDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        total_users = User.objects.filter(is_staff=False).count()
        total_products = Product.objects.count() if Product else 0
        total_orders = Order.objects.count() if Order else 0
        
        total_revenue = 0
        if Order:
            revenue_data = Order.objects.aggregate(Sum('total_price'))
            total_revenue = revenue_data.get('total_price__sum') or 0

        return Response({
            "total_users": total_users,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": total_revenue
        })


# ==========================================
# 9. ADMIN: User Management
# ==========================================
class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer
    # Using 'created_at' as per your custom user model
    queryset = User.objects.all().order_by('-created_at')

class AdminBlockUserView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        
        if user == request.user:
            return Response({"error": "You cannot block yourself"}, status=400)

        # Toggle Blocked State
        user.is_blocked = not user.is_blocked
        # Sync is_active to immediately kill standard sessions
        user.is_active = not user.is_blocked 
        user.save()
        
        return Response(AdminUserSerializer(user).data)

class AdminUpdateRoleView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        new_role = request.data.get("role")

        if user == request.user:
             return Response({"error": "You cannot change your own role"}, status=400)

        if new_role == "Admin":
            user.is_staff = True
        elif new_role == "User":
            user.is_staff = False
            user.is_superuser = False
        
        user.save()
        return Response(AdminUserSerializer(user).data)