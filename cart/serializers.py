from rest_framework import serializers
from .models import Cart, CartItem
from products.models import Product
from django.conf import settings 

# ----------------------------
# Product Mini Serializer
# ----------------------------
class ProductMiniSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()  # override image to return full URL

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "price",
            "image",
            "category",
        )

    def get_image(self, obj):
        if obj.image:
            # If using Cloudinary, obj.image might already be a URL
            try:
                return obj.image.url  # works for ImageField (local or Cloudinary)
            except ValueError:
                return obj.image  # fallback if already a URL
        return None


# ----------------------------
# Cart Item Serializer
# ----------------------------
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductMiniSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = (
            "id",
            "product",
            "quantity",
            "total_price",
        )

    def get_total_price(self, obj):
        return obj.quantity * obj.product.price


# ----------------------------
# Cart Serializer
# ----------------------------
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = (
            "id",
            "items",
            "total_amount",
            "created_at",
            "updated_at",
        )

    def get_total_amount(self, obj):
        return sum(item.quantity * item.product.price for item in obj.items.all())


# ----------------------------
# Add To Cart Serializer
# ----------------------------
class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
