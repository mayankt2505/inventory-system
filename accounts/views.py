from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect


def user_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    error_message = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active:
            login(request, user)
            return redirect("dashboard")
        else:
            error_message = "Invalid username or password."

    return render(request, "accounts/login.html", {"error_message": error_message})


def user_logout(request):
    logout(request)
    return redirect("login")