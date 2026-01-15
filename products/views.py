from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Product, ProductImage
from .serializers import ProductSerializer

# ==========================================
# 1. List All Products & Create New Product
# ==========================================
class ProductListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        """List all products (Public)"""
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new product (Admin Only)"""
        if not (request.user.is_staff or request.user.is_superuser):
             return Response({"detail": "You do not have permission to add products."}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            
            # Handle Multiple Gallery Images
            gallery_files = request.FILES.getlist('gallery_images')
            for file in gallery_files:
                ProductImage.objects.create(product=product, image=file)

            return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)
            
        print("❌ VALIDATION ERROR:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# 2. Retrieve, Update (Edit) & Delete Product
# ==========================================
class ProductDetailView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        """Get single product details (Public)"""
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def put(self, request, pk):
        """Full Edit Product (Admin Only)"""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            product = serializer.save()

            # Add NEW gallery images
            gallery_files = request.FILES.getlist('gallery_images')
            for file in gallery_files:
                ProductImage.objects.create(product=product, image=file)

            return Response(ProductSerializer(product).data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ✅ ADDED: Fixes the 405 Method Not Allowed Error
    def patch(self, request, pk):
        """Partial Edit Product (Admin Only)"""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # partial=True allows updating specific fields (like Brand) without sending everything
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            product = serializer.save()

            # Add NEW gallery images (if any)
            gallery_files = request.FILES.getlist('gallery_images')
            for file in gallery_files:
                ProductImage.objects.create(product=product, image=file)

            return Response(ProductSerializer(product).data)
            
        print("❌ UPDATE ERROR:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Delete Product (Admin Only)"""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)