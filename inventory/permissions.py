from django.http import HttpResponseForbidden


def is_admin(user):
    return user.is_authenticated and user.groups.filter(name="Admin").exists()


def is_special(user):
    return user.is_authenticated and user.groups.filter(name="special").exists()


def is_user_group(user):
    return user.is_authenticated and user.groups.filter(name="User").exists()


def can_manage_categories(user):
    return is_admin(user)


def can_manage_products(user):
    return is_admin(user) or is_special(user)


def can_manage_sales(user):
    return is_admin(user) or is_special(user)


def forbidden_response():
    return HttpResponseForbidden("You do not have permission to perform this action.")