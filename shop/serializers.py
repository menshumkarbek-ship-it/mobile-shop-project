from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class ProductSerializer(serializers.ModelSerializer):
    # Nest the category details inside the product serialization
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'brand', 'name', 'slug',
            'price', 'description', 'specifications', 'is_sold'
        ]