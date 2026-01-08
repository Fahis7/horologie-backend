from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'price', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'full_name', 'address', 'city', 'state', 
            'zip_code', 'phone', 'total_price', 'payment_id', 'status', 'items', 'created_at'
        ]
        read_only_fields = ['user', 'total_price', 'status', 'created_at']