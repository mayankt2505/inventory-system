from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Category, Product, Sale
from .forms import CategoryForm, ProductForm, SaleForm
from .permissions import (
    can_manage_categories,
    can_manage_products,
    can_manage_sales,
    forbidden_response,
)
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.contrib import messages

import csv
from django.http import HttpResponse

from django.db.models import Sum

@login_required
def dashboard(request):
    inventory_value_expr = ExpressionWrapper(
        F("quantity") * F("buy_price"),
        output_field=DecimalField(max_digits=15, decimal_places=2)
    )

    total_inventory_value = Product.objects.aggregate(
        total=Sum(inventory_value_expr)
    )["total"] or 0

    total_sales_revenue = Sale.objects.aggregate(
        total=Sum("price")
    )["total"] or 0

    low_stock_products = Product.objects.filter(quantity__lte=10).order_by("quantity")[:5]
    recent_sales = Sale.objects.select_related("product").order_by("-date", "-id")[:5]

    context = {
        "category_count": Category.objects.count(),
        "product_count": Product.objects.count(),
        "sale_count": Sale.objects.count(),
        "total_inventory_value": total_inventory_value,
        "total_sales_revenue": total_sales_revenue,
        "low_stock_products": low_stock_products,
        "recent_sales": recent_sales,
    }
    return render(request, "inventory/dashboard.html", context)

@login_required
def category_list(request):
    categories = Category.objects.all()
    context = {
        "categories": categories,
        "can_manage_categories": can_manage_categories(request.user),
    }
    return render(request, "inventory/category_list.html", context)


@login_required
def product_list(request):
    products = Product.objects.select_related("category", "media").all()
    categories = Category.objects.all()

    search_query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()

    if search_query:
        products = products.filter(name__icontains=search_query)

    if category_id:
        products = products.filter(category_id=category_id)

    context = {
        "products": products,
        "categories": categories,
        "search_query": search_query,
        "selected_category": category_id,
    }
    return render(request, "inventory/product_list.html", context)

@login_required
def sale_list(request):
    sales = Sale.objects.select_related("product").all()

    search_query = request.GET.get("q", "").strip()
    from_date = request.GET.get("from_date", "").strip()
    to_date = request.GET.get("to_date", "").strip()

    if search_query:
        sales = sales.filter(product__name__icontains=search_query)

    if from_date:
        sales = sales.filter(date__gte=from_date)

    if to_date:
        sales = sales.filter(date__lte=to_date)

    sales = sales.order_by("-date", "-id")

    context = {
        "sales": sales,
        "search_query": search_query,
        "from_date": from_date,
        "to_date": to_date,
    }
    return render(request, "inventory/sale_list.html", context)


@login_required
def add_category(request):
    if not can_manage_categories(request.user):
        return forbidden_response()

    form = CategoryForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Category added successfully.")
        return redirect("category_list")
    return render(request, "inventory/add_category.html", {"form": form})

@login_required
def edit_category(request, id):
    if not can_manage_categories(request.user):
        return forbidden_response()

    category = get_object_or_404(Category, id=id)
    form = CategoryForm(request.POST or None, instance=category)

    if form.is_valid():
        form.save()
        messages.success(request, "Category updated successfully.")
        return redirect("category_list")

    return render(request, "inventory/add_category.html", {"form": form})

@login_required
def delete_category(request, id):
    if not can_manage_categories(request.user):
        return forbidden_response()

    category = get_object_or_404(Category, id=id)

    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted successfully.")
        return redirect("category_list")

    return render(request, "inventory/confirm_delete.html", {
        "object": category,
        "type": "Category",
        "cancel_url": "category_list",
    })


@login_required
def add_product(request):
    if not can_manage_products(request.user):
        return forbidden_response()

    form = ProductForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Product added successfully.")
        return redirect("product_list")
    return render(request, "inventory/add_product.html", {"form": form})


@login_required
def edit_product(request, id):
    if not can_manage_products(request.user):
        return forbidden_response()

    product = get_object_or_404(Product, id=id)
    form = ProductForm(request.POST or None, instance=product)

    if form.is_valid():
        form.save()
        messages.success(request, "Product updated successfully.")
        return redirect("product_list")

    return render(request, "inventory/add_product.html", {"form": form})


@login_required
def delete_product(request, id):
    if not can_manage_products(request.user):
        return forbidden_response()

    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully.")
        return redirect("product_list")

    return render(request, "inventory/confirm_delete.html", {
        "object": product,
        "type": "Product",
        "cancel_url": "product_list",
    })


@login_required
def add_sale(request):
    if not can_manage_sales(request.user):
        return forbidden_response()

    form = SaleForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Sale added successfully.")
        return redirect("sale_list")
    return render(request, "inventory/add_sale.html", {"form": form})

@login_required
def edit_sale(request, id):
    if not can_manage_sales(request.user):
        return forbidden_response()

    sale = get_object_or_404(Sale, id=id)
    form = SaleForm(request.POST or None, instance=sale)

    if form.is_valid():
        form.save()
        messages.success(request, "Sale updated successfully.")
        return redirect("sale_list")

    return render(request, "inventory/add_sale.html", {"form": form})


@login_required
def delete_sale(request, id):
    if not can_manage_sales(request.user):
        return forbidden_response()

    sale = get_object_or_404(Sale, id=id)

    if request.method == "POST":
        sale.delete()
        messages.success(request, "Sale deleted successfully.")
        return redirect("sale_list")

    return render(request, "inventory/confirm_delete.html", {
        "object": sale,
        "type": "Sale",
        "cancel_url": "sale_list",
    })
    

@login_required
def export_products_csv(request):
    if not can_manage_products(request.user):
        return forbidden_response()

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="products.csv"'

    writer = csv.writer(response)
    writer.writerow(["ID", "Name", "Quantity", "Buy Price", "Sale Price", "Category"])

    products = Product.objects.select_related("category").all().order_by("id")

    for product in products:
        writer.writerow([
            product.id,
            product.name,
            product.quantity,
            product.buy_price,
            product.sale_price,
            product.category.name,
        ])

    return response


@login_required
def export_sales_csv(request):
    if not can_manage_sales(request.user):
        return forbidden_response()

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="sales.csv"'

    writer = csv.writer(response)
    writer.writerow(["ID", "Product", "Quantity", "Price", "Date"])

    sales = Sale.objects.select_related("product").all().order_by("-date", "-id")

    for sale in sales:
        writer.writerow([
            sale.id,
            sale.product.name,
            sale.qty,
            sale.price,
            sale.date,
        ])

    return response

@login_required
def sales_summary_report(request):
    if not can_manage_sales(request.user):
        return forbidden_response()

    from_date = request.GET.get("from_date", "").strip()
    to_date = request.GET.get("to_date", "").strip()

    sales = Sale.objects.select_related("product").all()

    if from_date:
        sales = sales.filter(date__gte=from_date)

    if to_date:
        sales = sales.filter(date__lte=to_date)

    revenue_expr = ExpressionWrapper(
        F("qty") * F("price"),
        output_field=DecimalField(max_digits=15, decimal_places=2)
    )

    summary = (
        sales.values("product__id", "product__name")
        .annotate(
            total_qty_sold=Sum("qty"),
            total_revenue=Sum(revenue_expr),
        )
        .order_by("-total_revenue", "-total_qty_sold")
    )

    context = {
        "summary": summary,
        "from_date": from_date,
        "to_date": to_date,
    }

    return render(request, "inventory/sales_summary_report.html", context)