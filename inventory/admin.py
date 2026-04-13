from django.contrib import admin
from .models import Category, ProductMedia, Product, Sale

admin.site.register(Category)
admin.site.register(ProductMedia)
admin.site.register(Product)
admin.site.register(Sale)