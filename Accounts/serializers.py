from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.cache import cache 

User = get_user_model()

# ... [Keep UserSerializer, RegisterSerializer, AdminUserSerializer exactly as they were] ...

class UserSerializer(serializers.ModelSerializer):
    cart = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "email", "phone_number", "first_name", "last_name",
            "is_staff", "is_superuser", "is_active", "cart",
        )

    def get_cart(self, obj):
        try:
            from cart.serializers import CartSerializer
            if hasattr(obj, 'cart'):
                return CartSerializer(obj.cart).data
        except ImportError:
            return None
        return None

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class AdminUserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(source='created_at', read_only=True) 

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'role', 'is_blocked', 'date_joined']

    def get_role(self, obj):
        return "Admin" if obj.is_staff else "User"

    def get_name(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name if full_name else obj.email.split('@')[0]


# ==========================================
#  CORRECTED: OTP Password Reset Serializers
# ==========================================

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    # REMOVED: validate_email method. 
    # We now accept ANY email format here so we don't throw a 400 error.
    # The actual check happens silently in the View.


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        email = attrs.get('email')
        otp = attrs.get('otp')
        
        # 1. Check if OTP is in Cache
        cached_otp = cache.get(f'otp_{email}')
        
        if cached_otp is None:
             raise serializers.ValidationError("The OTP has expired or is invalid. Please request a new one.")
        
        # 2. Verify OTP matches
        if cached_otp != otp:
             raise serializers.ValidationError("Invalid OTP code.")
        
        return attrs

    def save(self):
        email = self.validated_data['email']
        new_password = self.validated_data['new_password']
        
        # 3. Reset Password
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        
        # 4. Clear Cache
        cache.delete(f'otp_{email}')
        
        return user