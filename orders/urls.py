from django.urls import path
from .views import CreateOrderView, OrderListView, CreatePaymentIntentView,AdminOrderUpdateView,AdminOrderListView,CancelOrderView

urlpatterns = [
    path('create-payment-intent/', CreatePaymentIntentView.as_view()),
    path('create/', CreateOrderView.as_view()),
    path('my-orders/', OrderListView.as_view()),
    
    path('admin/all/', AdminOrderListView.as_view(), name='admin-orders-list'),
    path('admin/update/<int:pk>/', AdminOrderUpdateView.as_view(), name='admin-order-update'),
    path('<int:pk>/cancel/', CancelOrderView.as_view(), name='user-cancel-order'),
]