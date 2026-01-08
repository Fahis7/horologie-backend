import stripe
from django.conf import settings
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import  permissions, generics
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem
from .serializers import OrderSerializer
from cart.models import Cart

stripe.api_key = settings.STRIPE_SECRET_KEY

# 1. Initialize Stripe Payment
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

# 2. Save the Order
class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data
        
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

                # ✅ SEND EMAIL
                self.send_confirmation_email(user, order)

            serializer = OrderSerializer(order)
            return Response(serializer.data, status=201)

        except Exception as e:
            print(f"Order Creation Error: {e}")
            return Response({"detail": str(e)}, status=500)

    # EMAIL CONTENT
    def send_confirmation_email(self, user, order):
        try:
            dashboard_link = "http://localhost:5173/orders"

            subject = f"CONFIRMED: Your Acquisition | Order #{order.id}"
            
            message = f"""
Dear {user.first_name},

It is with distinct pleasure that we confirm your recent acquisition from the Horologie Maison.

You have not merely purchased a timepiece; you have secured a legacy. 
Our master horologists in the atelier are currently performing the final precision checks on your selection to ensure it meets our exacting standards of excellence before it begins its journey to you.

Your investment details are securely recorded below:

------------------------------------------------------
ACQUISITION REFERENCE: #{order.id}
TOTAL INVESTMENT: ₹{order.total_price}
------------------------------------------------------

OFFICIAL DOCUMENTATION
In recognition of this acquisition, an official Digital Certificate of Authenticity has been minted in your name. 
This document serves as immutable proof of ownership for your private records.

"Your digital Certificate of Authenticity has been minted. You may access and securely download it from your private vault:"
{dashboard_link}

We remain at your service.

Yours in Excellence,

The Horologie Private Concierge
New York | Geneva | Tokyo
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

# 3. List User Orders
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')