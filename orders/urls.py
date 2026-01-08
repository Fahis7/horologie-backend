from django.urls import path
from .views import CreateOrderView, OrderListView, CreatePaymentIntentView

urlpatterns = [
    path('create-payment-intent/', CreatePaymentIntentView.as_view()),
    path('create/', CreateOrderView.as_view()),
    path('', OrderListView.as_view()),
]