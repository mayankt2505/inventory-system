import ast
import re
from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

from inventory.models import Category, ProductMedia, Product, Sale
from accounts.models import UserProfile


class Command(BaseCommand):
    help = "Import legacy MySQL dump into Django models"

    def handle(self, *args, **kwargs):
        sql_path = "data/inventory_system.sql"

        with open(sql_path, "r", encoding="utf-8") as f:
            sql_text = f.read()

        self.import_categories(sql_text)
        self.import_media(sql_text)
        self.import_products(sql_text)
        self.import_groups(sql_text)
        self.import_users(sql_text)
        self.import_sales(sql_text)

        self.stdout.write(self.style.SUCCESS("Legacy SQL import completed successfully."))

    def extract_rows(self, sql_text, table_name):
        pattern = rf"INSERT INTO `{table_name}` .*? VALUES\s*(.*?);"
        match = re.search(pattern, sql_text, re.S)

        if not match:
            return []

        values_block = match.group(1).strip()
        tuple_strings = re.findall(r"\(.*?\)", values_block, re.S)

        rows = []
        for tup in tuple_strings:
            python_tuple = tup.replace("NULL", "None")
            rows.append(ast.literal_eval(python_tuple))

        return rows

    def import_categories(self, sql_text):
        rows = self.extract_rows(sql_text, "categories")

        for row in rows:
            obj_id, name = row
            Category.objects.update_or_create(
                id=obj_id,
                defaults={
                    "name": name
                }
            )

        self.stdout.write(self.style.SUCCESS(f"Imported {len(rows)} categories"))

    def import_media(self, sql_text):
        rows = self.extract_rows(sql_text, "media")

        for row in rows:
            obj_id, file_name, file_type = row
            ProductMedia.objects.update_or_create(
                id=obj_id,
                defaults={
                    "file_name": file_name,
                    "file_type": file_type,
                }
            )

        self.stdout.write(self.style.SUCCESS(f"Imported {len(rows)} media rows"))

    def import_products(self, sql_text):
        rows = self.extract_rows(sql_text, "products")

        for row in rows:
            obj_id, name, quantity, buy_price, sale_price, categorie_id, media_id, created_at = row

            Product.objects.update_or_create(
                id=obj_id,
                defaults={
                    "name": name,
                    "quantity": int(quantity) if quantity else 0,
                    "buy_price": Decimal(str(buy_price)) if buy_price is not None else None,
                    "sale_price": Decimal(str(sale_price)),
                    "category_id": int(categorie_id),
                    "media_id": None if media_id in (0, "0", None) else int(media_id),
                    "created_at": datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S"),
                }
            )

        self.stdout.write(self.style.SUCCESS(f"Imported {len(rows)} products"))

    def import_groups(self, sql_text):
        rows = self.extract_rows(sql_text, "user_groups")

        for row in rows:
            obj_id, group_name, group_level, group_status = row

            if int(group_status) != 1:
                continue

            Group.objects.get_or_create(name=group_name)

        self.stdout.write(self.style.SUCCESS("Imported active groups"))

    def import_users(self, sql_text):
        rows = self.extract_rows(sql_text, "users")

        level_to_group = {
            1: "Admin",
            2: "special",
            3: "User",
        }

        for row in rows:
            obj_id, name, username, password_hash, user_level, image, status, last_login = row

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": name,
                    "is_active": bool(status),
                }
            )

            if not created:
                user.first_name = name
                user.is_active = bool(status)

            if int(user_level) == 1:
                temp_password = "Admin@123"
            elif int(user_level) == 2:
                temp_password = "Special@123"
            else:
                temp_password = "User@123"

            user.set_password(temp_password)
            user.save()

            user.groups.clear()

            group_name = level_to_group.get(int(user_level))
            if group_name:
                group, _ = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.image = image or "no_image.jpg"
            profile.status = bool(status)
            profile.legacy_user_level = int(user_level)
            profile.last_login_at = (
                datetime.strptime(last_login, "%Y-%m-%d %H:%M:%S")
                if last_login else None
            )
            profile.save()

        self.stdout.write(self.style.SUCCESS(f"Imported {len(rows)} users"))

    def import_sales(self, sql_text):
        rows = self.extract_rows(sql_text, "sales")

        existing_ids = set(Sale.objects.values_list("id", flat=True))
        sales_to_create = []

        for row in rows:
            obj_id, product_id, qty, price, sale_date = row

            if int(obj_id) in existing_ids:
                continue

            sales_to_create.append(
                Sale(
                    id=int(obj_id),
                    product_id=int(product_id),
                    qty=int(qty),
                    price=Decimal(str(price)),
                    date=datetime.strptime(sale_date, "%Y-%m-%d").date(),
                )
            )

        if sales_to_create:
            Sale.objects.bulk_create(sales_to_create)

        self.stdout.write(self.style.SUCCESS(f"Imported {len(sales_to_create)} sales"))