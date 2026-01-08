from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Cart, CartItem
from .serializers import AddToCartSerializer, CartSerializer
from products.models import Product


class CartDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AddToCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        quantity = serializer.validated_data["quantity"]

        # Get product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Stock validation
        if quantity > product.stock:
            return Response(
                {"detail": "Not enough stock available"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create cart
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # Get or create cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product
        )

        if not created:
            if cart_item.quantity + quantity > product.stock:
                return Response(
                    {"detail": "Stock limit exceeded"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity

        cart_item.save()

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK
        )


class UpdateCartItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        quantity = request.data.get("quantity")

        if not quantity or int(quantity) < 1:
            return Response(
                {"detail": "Quantity must be at least 1"},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart = Cart.objects.filter(user=request.user).first()
        if not cart:
            return Response(
                {"detail": "Cart not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        cart_item = CartItem.objects.filter(
            id=item_id,
            cart=cart
        ).first()

        if not cart_item:
            return Response(
                {"detail": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if int(quantity) > cart_item.product.stock:
            return Response(
                {"detail": "Stock limit exceeded"},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = int(quantity)
        cart_item.save()

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK
        )


class RemoveFromCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        cart = Cart.objects.filter(user=request.user).first()
        if not cart:
            return Response(
                {"detail": "Cart not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        cart_item = CartItem.objects.filter(
            id=item_id,
            cart=cart
        ).first()

        if not cart_item:
            return Response(
                {"detail": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        cart_item.delete()

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK
        )


class ClearCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart.items.all().delete()

        return Response(
            {"message": "Cart cleared successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
