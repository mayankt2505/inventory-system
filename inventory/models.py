from django.db import models, transaction
from django.core.exceptions import ValidationError


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        db_table = "categories"

    def __str__(self):
        return self.name


class ProductMedia(models.Model):
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)

    class Meta:
        db_table = "media"

    def __str__(self):
        return self.file_name


class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    quantity = models.IntegerField(null=True, blank=True)
    buy_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    media = models.ForeignKey(ProductMedia, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "products"

    def __str__(self):
        return self.name


class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales")
    qty = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()

    class Meta:
        db_table = "sales"

    def __str__(self):
        return f"{self.product.name} - {self.qty}"

    def clean(self):
        if self.qty is None or self.qty <= 0:
            raise ValidationError({"qty": "Quantity must be greater than 0."})

        if not self.product_id:
            return

        old_qty = 0
        old_product_id = None

        if self.pk:
            old_sale = Sale.objects.get(pk=self.pk)
            old_qty = old_sale.qty
            old_product_id = old_sale.product_id

        if old_product_id == self.product_id:
            available = (self.product.quantity or 0) + old_qty
            if self.qty > available:
                raise ValidationError({"qty": f"Not enough stock. Available: {available}"})
        else:
            available = self.product.quantity or 0
            if self.qty > available:
                raise ValidationError({"qty": f"Not enough stock. Available: {available}"})

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.full_clean()

        if self.pk:
            old_sale = Sale.objects.select_for_update().get(pk=self.pk)
            old_product = Product.objects.select_for_update().get(pk=old_sale.product_id)
            new_product = Product.objects.select_for_update().get(pk=self.product_id)

            if old_product.id == new_product.id:
                old_product.quantity = (old_product.quantity or 0) + old_sale.qty - self.qty
                old_product.save(update_fields=["quantity"])
            else:
                old_product.quantity = (old_product.quantity or 0) + old_sale.qty
                old_product.save(update_fields=["quantity"])

                new_product.quantity = (new_product.quantity or 0) - self.qty
                new_product.save(update_fields=["quantity"])

            super().save(*args, **kwargs)

        else:
            product = Product.objects.select_for_update().get(pk=self.product_id)
            product.quantity = (product.quantity or 0) - self.qty
            product.save(update_fields=["quantity"])
            super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        product = Product.objects.select_for_update().get(pk=self.product_id)
        product.quantity = (product.quantity or 0) + self.qty
        product.save(update_fields=["quantity"])
        super().delete(*args, **kwargs)