from django.core.management.base import BaseCommand
from django.utils.text import slugify
from shop.models import Category, Product

class Command(BaseCommand):
    help = 'Pre-populates the database with default categories and tech items'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding database setup...")

        # 1. Create Base Categories
        laptop_cat, _ = Category.objects.get_or_create(name="Laptop", slug="laptops")
        phone_cat, _ = Category.objects.get_or_create(name="Mobile Phone", slug="mobile-phones")

        # 2. Mock Laptop & Mobile Data with specifications JSON
        products_data = [
            {
                "category": laptop_cat,
                "brand": "Apple",
                "name": "MacBook Pro 16 M3",
                "price": 2499.99,
                "description": "Supercharged by M3 Pro or M3 Max. Stunning Liquid Retina XDR display.",
                "specifications": {"CPU": "M3 Pro 12-Core", "RAM": "18GB", "Storage": "512GB SSD", "Color": "Space Black"}
            },
            {
                "category": laptop_cat,
                "brand": "ASUS",
                "name": "ROG Zephyrus G14",
                "price": 1599.99,
                "description": "High-performance AMD Ryzen 9 gaming laptop with an OLED display.",
                "specifications": {"CPU": "Ryzen 9", "GPU": "RTX 4070", "RAM": "16GB DDR5", "Storage": "1TB NVMe"}
            },
            {
                "category": phone_cat,
                "brand": "Apple",
                "name": "iPhone 15 Pro",
                "price": 999.99,
                "description": "Forged in titanium, featuring the groundbreaking A17 Pro chip.",
                "specifications": {"Chipset": "A17 Pro", "Storage": "128GB", "Camera": "48MP Main", "Screen": "6.1-inch"}
            },
            {
                "category": phone_cat,
                "brand": "Samsung",
                "name": "Galaxy S24 Ultra",
                "price": 1299.99,
                "description": "Welcome to the era of mobile AI. Built with a sleek titanium armor layer.",
                "specifications": {"Chipset": "Snapdragon 8 Gen 3", "Storage": "256GB", "RAM": "12GB", "Stylus": "S-Pen Included"}
            }
        ]

        # 3. Save mock items to your local PostgreSQL database
        for item in products_data:
            product, created = Product.objects.get_or_create(
                name=item["name"],
                category=item["category"],
                defaults={
                    "brand": item["brand"],
                    "slug": slugify(f"{item['brand']}-{item['name']}"),
                    "price": item["price"],
                    "description": item["description"],
                    "specifications": item["specifications"],
                    "is_sold": False
                }
            )
            if created:
                self.stdout.write(f"Successfully added product: {item['name']}")

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))