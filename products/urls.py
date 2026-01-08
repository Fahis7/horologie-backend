# products/urls.py
from django.urls import path
from .views import ProductListView, ProductCreateView, ProductDetailView

urlpatterns = [
    path("", ProductListView.as_view()),  # /api/products/
    path("create/", ProductCreateView.as_view()),  # /api/products/create/
    path("<int:pk>/", ProductDetailView.as_view()),  # /api/products/<id>/
]
