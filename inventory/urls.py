from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("categories/", views.category_list, name="category_list"),
    path("categories/add/", views.add_category, name="add_category"),
    path("categories/edit/<int:id>/", views.edit_category, name="edit_category"),
    path("categories/delete/<int:id>/", views.delete_category, name="delete_category"),

    path("products/", views.product_list, name="product_list"),
    path("products/add/", views.add_product, name="add_product"),
    path("products/edit/<int:id>/", views.edit_product, name="edit_product"),
    path("products/delete/<int:id>/", views.delete_product, name="delete_product"),

    path("sales/", views.sale_list, name="sale_list"),
    path("sales/add/", views.add_sale, name="add_sale"),
    path("sales/edit/<int:id>/", views.edit_sale, name="edit_sale"),
    path("sales/delete/<int:id>/", views.delete_sale, name="delete_sale"),
    path("products/export/csv/", views.export_products_csv, name="export_products_csv"),
path("sales/export/csv/", views.export_sales_csv, name="export_sales_csv"),
path("sales/report/summary/", views.sales_summary_report, name="sales_summary_report"),
]
