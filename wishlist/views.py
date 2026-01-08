from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Wishlist
from .serializers import WishlistSerializer
from products.models import Product

# GET: List all items ,, POST: Add item
class WishlistListCreateView(generics.ListCreateAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).order_by('-added_at')

    def perform_create(self, serializer):
        # If item already exists, do nothing
        product = serializer.validated_data['product']
        if not Wishlist.objects.filter(user=self.request.user, product=product).exists():
            serializer.save(user=self.request.user)

# DELETE: Remove item by Product ID
class WishlistToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, product_id):
        item = get_object_or_404(Wishlist, user=request.user, product_id=product_id)
        item.delete()
        return Response({"message": "Removed from wishlist"}, status=status.HTTP_204_NO_CONTENT)