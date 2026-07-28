from django.db import models
from django.contrib.auth.models import User


# 1. Extending the default User model for detailed signup info (Passport, Phone)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    passport_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Required for customer identity verification"
    )
    registration_date = models.DateTimeField(auto_now_add=True)

    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.user.username})"


# 2. Product Categories (Laptops vs. Mobile Phones)
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)  # e.g., 'Laptop' or 'Mobile Phone'
    slug = models.SlugField(max_length=100, unique=True)  # e.g., 'laptops' or 'mobile-phones'

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


# 3. Main Product catalog with "Sold" and specification tracking
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.CharField(max_length=100, help_text="e.g., Acer, ASUS, Apple, HP, Samsung")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    # Stores laptop-specific or phone-specific attributes (RAM, CPU, Screen, Battery)
    specifications = models.JSONField(
        default=dict,
        help_text="Store characteristics as JSON. (e.g., {'RAM': '16GB', 'CPU': 'M3'})"
    )

    # Real-time stock filter: True means it is sold and must be hidden from the UI
    is_sold = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "SOLD" if self.is_sold else "AVAILABLE"
        return f"[{status}] {self.brand} - {self.name}"

from django.conf import settings
from django.db import models

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.PROTECT) # Protect ensures historical sales data isn't deleted
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.order.id})"