from django.urls import path
from .views import (
    CartDetailAPIView,
    AddToCartAPIView,
    RemoveFromCartAPIView,
    UpdateCartItemAPIView,
    ClearCartAPIView,
)

urlpatterns = [
    path("", CartDetailAPIView.as_view()),
    path("add/", AddToCartAPIView.as_view()),
    path("remove/<int:item_id>/", RemoveFromCartAPIView.as_view()),
    path("update/<int:item_id>/", UpdateCartItemAPIView.as_view()),
    path("clear/", ClearCartAPIView.as_view()),
]
