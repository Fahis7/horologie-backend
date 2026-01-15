from django.urls import path
from .views import ProductListCreateView, ProductDetailView

urlpatterns = [
    # 1. GET /api/products/ -> List All
    # 2. POST /api/products/ -> Create New (Admin only)
    path("", ProductListCreateView.as_view(), name="product-list-create"),

    # 1. GET /api/products/<id>/ -> Retrieve Single
    # 2. PUT /api/products/<id>/ -> Edit (Admin only)
    # 3. DELETE /api/products/<id>/ -> Delete (Admin only)
    path("<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
]   