from django.contrib import admin
from .models import UserProfile, Category, Product

# Admin styling for Products
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'price', 'is_sold', 'created_at')
    list_filter = ('is_sold', 'category', 'brand') # Let admin filter sold/unsold quickly
    search_fields = ('name', 'brand', 'description')
    prepopulated_fields = {'slug': ('name',)} # Automatically generates slugs as you type names

admin.site.register(Category)
admin.site.register(UserProfile)