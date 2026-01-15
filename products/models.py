from django.db import models
from cloudinary.models import CloudinaryField

class Product(models.Model):
    CATEGORY_CHOICES = (
        ("men", "Men"),
        ("women", "Women"),
    )

    #  1. Add Brand Choices
    BRAND_CHOICES = (
        ("Rolex", "Rolex"),
        ("Rado", "Rado"),
        ("Patek Philippe", "Patek Philippe"),
        ("Audemars Piguet", "Audemars Piguet"),
        ("Omega", "Omega"),
        ("Cartier", "Cartier"),
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)

    brand = models.CharField(
        max_length=50, 
        choices=BRAND_CHOICES, 
        default="Rolex" # Default needed for existing items
    )

    # Main Image
    image = CloudinaryField("image", folder="products")
    video = models.URLField(max_length=2000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Gallery Images (No changes)
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='gallery', on_delete=models.CASCADE)
    image = CloudinaryField("image", folder="products")

    def __str__(self):
        return f"{self.product.name} Image"