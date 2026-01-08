from django.db import models
from cloudinary.models import CloudinaryField

class Product(models.Model):

    CATEGORY_CHOICES = (
        ("men", "Men"),
        ("women", "Women"),
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()

    category = models.CharField(
        max_length=10,
        choices=CATEGORY_CHOICES
    )

    image = CloudinaryField("image", folder="products")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
