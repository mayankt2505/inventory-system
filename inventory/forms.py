from django import forms
from .models import Category, Product, Sale


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "quantity", "buy_price", "sale_price", "category", "media"]


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["product", "qty", "price", "date"]