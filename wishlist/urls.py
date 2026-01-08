from django.urls import path
from .views import WishlistListCreateView, WishlistToggleView

urlpatterns = [
    path('', WishlistListCreateView.as_view()),             # GET /api/wishlist/ or POST
    path('remove/<int:product_id>/', WishlistToggleView.as_view()), # DELETE /api/wishlist/remove/5/
]