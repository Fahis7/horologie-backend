from rest_framework import serializers
from .models import User

# Try importing CartSerializer (handling circular imports)
try:
    from cart.serializers import CartSerializer
except ImportError:
    CartSerializer = None

class UserSerializer(serializers.ModelSerializer):
    cart = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone_number",  # <--- ADDED THIS NEW FIELD
            "first_name",
            "last_name",
            "is_staff",
            "is_active",
            "cart",
        )

    def get_cart(self, obj):
        if CartSerializer and hasattr(obj, 'cart'):
            return CartSerializer(obj.cart).data
        return None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)