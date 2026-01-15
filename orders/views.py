import stripe
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, generics, status
from rest_framework.permissions import IsAdminUser

from .models import Order, OrderItem
from .serializers import OrderSerializer
from cart.models import Cart

stripe.api_key = settings.STRIPE_SECRET_KEY

# ==========================================
# 1. CUSTOMER: Initialize Stripe Payment
# ==========================================
class CreatePaymentIntentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            cart = Cart.objects.get(user=user)
            if not cart.items.exists():
                return Response({'error': 'Cart is empty'}, status=400)
            
            total_amount = sum(item.product.price * item.quantity for item in cart.items.all())
            
            intent = stripe.PaymentIntent.create(
                amount=int(total_amount * 100), 
                currency='inr', 
                metadata={'user_id': user.id}
            )

            return Response({'clientSecret': intent['client_secret']})
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)

# ==========================================
# 2. CUSTOMER: Create Order (Checkout)
# ==========================================
class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data
        
        # Safe get cart
        cart = get_object_or_404(Cart, user=user)
        cart_items = cart.items.all()
        
        if not cart_items.exists():
            return Response({"detail": "Cart is empty"}, status=400)

        total_price = sum(item.product.price * item.quantity for item in cart_items)

        try:
            with transaction.atomic():
                # Create Order
                order = Order.objects.create(
                    user=user,
                    full_name=data.get('full_name'),
                    address=data.get('address'),
                    city=data.get('city'),
                    state=data.get('state'),
                    zip_code=data.get('zip_code'),
                    phone=data.get('phone'),
                    total_price=total_price,
                    payment_id=data.get('payment_id')
                )

                # Move items
                order_items = [
                    OrderItem(
                        order=order,
                        product=item.product,
                        price=item.product.price,
                        quantity=item.quantity
                    ) for item in cart_items
                ]
                OrderItem.objects.bulk_create(order_items)

                # Clear Cart
                cart_items.delete()

                # Send Email
                self.send_confirmation_email(user, order)

            serializer = OrderSerializer(order)
            return Response(serializer.data, status=201)

        except Exception as e:
            print(f"Order Creation Error: {e}")
            return Response({"detail": str(e)}, status=500)

    def send_confirmation_email(self, user, order):
        try:
            dashboard_link = "http://localhost:5173/orders"
            subject = f"CONFIRMED: Your Acquisition | Order #{order.id}"
            
            message = f"""
Dear {user.name},

It is with distinct pleasure that we confirm your recent acquisition from the Horologie Maison.

Your investment details are securely recorded below:
------------------------------------------------------
ACQUISITION REFERENCE: #{order.id}
TOTAL INVESTMENT: ₹{order.total_price}
------------------------------------------------------

"Your digital Certificate of Authenticity has been minted. You may access it from your private vault:"
{dashboard_link}

Yours in Excellence,
The Horologie Private Concierge
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True, 
            )
            print(f"✅ Email sent to {user.email}")
            
        except Exception as e:
            print(f"❌ Email failed: {str(e)}")

# ==========================================
# 3. CUSTOMER: List My Orders
# ==========================================
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

# ==========================================
# 4. ADMIN: List ALL Orders (Dashboard)
# ==========================================
class AdminOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser] 

    def get_queryset(self):
        return Order.objects.all().order_by('-created_at')

# ==========================================
# 5. ADMIN: Update Order Status (With Locking)
# ==========================================
class AdminOrderUpdateView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        new_status = request.data.get('status')
        
        if not new_status:
            return Response({"error": "Status is required"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ LOGIC: Prevent changing status if final
        if order.status == 'delivered':
            return Response({"error": "Cannot change status of a delivered order."}, status=400)
        
        if order.status == 'cancelled':
             return Response({"error": "Cannot change status of a cancelled order."}, status=400)

        order.status = new_status
        order.save()
        return Response(OrderSerializer(order).data)

# ==========================================
# 6. CUSTOMER: Cancel Order (New)
# ==========================================
class CancelOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        # Ensure users can only cancel THEIR OWN orders
        order = get_object_or_404(Order, pk=pk, user=request.user)

        # ✅ Check eligibility
        if order.status in ['shipped', 'delivered', 'cancelled']:
            return Response(
                {"error": f"Cannot cancel order that is already {order.status}"}, 
                status=400
            )

        order.status = 'cancelled'
        order.save()
        
        # Optional: Add refund logic here if payment was made
        
        return Response(OrderSerializer(order).data)