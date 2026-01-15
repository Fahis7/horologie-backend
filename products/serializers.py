from rest_framework import serializers
from .models import Product, ProductImage

# 1. Serializer for the Gallery Images
class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField() 
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image']
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            representation['image'] = instance.image.url
        return representation

# 2. Main Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    
    # Nest the gallery serializer
    gallery = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        # ✅ "__all__" will now include the new 'brand' field automatically
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            representation['image'] = instance.image.url
        return representation