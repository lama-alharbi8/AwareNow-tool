from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import CompanyForm
from django.contrib.auth.decorators import login_required
import uuid
from .forms import SuperAdminForm
from .models import Company
from .services import send_activation_email
from django.shortcuts import get_object_or_404

# ==== admin platform login ====
@login_required
def platform_dashboard(request):
    if not request.user.is_superuser:
        return redirect("account:platform-login")

    return render(request, "account/platform_dashboard.html")

def platform_login(request):
    # اذا مسجل دخول ينقله لصفحة الدشبورد للبلاتفورم 
    # if request.user.is_authenticated and request.user.is_superuser:
    #     return redirect("account:platform-dashboard")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user and user.is_superuser:
            login(request, user)
            return redirect("account:platform-dashboard")

        return render(request, "account/login.html", {
            "error": "Invalid credentials or not a platform admin"
        })

    return render(request, "account/login.html")

# ==== admin platform create company ====
@login_required
def create_company(request):
    if not request.user.is_superuser:
        return redirect("account:platform-login")

    if request.method == "POST":
        form = CompanyForm(request.POST)
        if form.is_valid():
            # company = form.save()
            company = form.save(commit=False)
            company.save()
            # create superadmin for company
            return redirect("account:create-super-admin", company_id=company.id)
    else:
        form = CompanyForm()

    return render(request, "account/create_company.html", {"form": form})

@login_required
def create_super_admin(request, company_id):
    if not request.user.is_superuser:
        return redirect("account:platform-login")

    company = get_object_or_404(Company, id=company_id)

    if request.method == "POST":
        form = SuperAdminForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = "COMPANY_ADMIN"
            user.company = company
            user.is_active = False
            user.set_unusable_password()
            user.activation_token = uuid.uuid4()
            user.save()

            send_activation_email(user)

            return render(request, "account/super_admin_created.html", {
                "email": user.email
            })
    else:
        form = SuperAdminForm()

    return render(request, "account/create_super_admin.html", {
        "form": form,
        "company": company
    })



