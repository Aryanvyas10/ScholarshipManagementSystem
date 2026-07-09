from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import hashlib
import random


from .models import Scholarship, ScholarshipApplication, PasswordResetOTP


def home(request):
    return render(request, "index.html")



@login_required(login_url="signin")
def dashboard(request):
    scholarships = Scholarship.objects.all()

    # Simple counters for the existing dashboard cards
    apps = ScholarshipApplication.objects.filter(applicant=request.user)
    context = {
        "scholarships": scholarships,
        "applications_new": apps.filter(status=ScholarshipApplication.Status.NEW).count(),
        "applications_approved": apps.filter(status=ScholarshipApplication.Status.APPROVED).count(),
        "applications_disbursed": apps.filter(status=ScholarshipApplication.Status.DISBURSED).count(),
        "applications_rejected": apps.filter(status=ScholarshipApplication.Status.REJECTED).count(),
        "applications_total": apps.count(),
        "applications_waiting": apps.filter(status=ScholarshipApplication.Status.WAITING_DISBURSEMENT).count(),
        "total_users": User.objects.count(),
        "total_schemes": scholarships.count(),
    }
    return render(request, "dashboard.html", context)


def add_scholarship(request):
    if not request.user.is_authenticated:
        return redirect("signin")
    if not request.user.is_staff:
        return redirect("dashboard")

    if request.method == "POST":
        scholarship = Scholarship(
            name=request.POST.get("name"),
            type_of_scholarship=request.POST.get("type_of_scholarship"),
            grade=request.POST.get("grade"),
            year=request.POST.get("year"),
            category=request.POST.get("category"),
            criteria=request.POST.get("criteria"),
            documents_required=request.POST.get("documents"),
        )
        scholarship.save()
        return redirect("dashboard")

    return render(request, "add_scholarship.html")


def delete_scholarship(request, id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect("dashboard")

    scholarship = get_object_or_404(Scholarship, id=id)
    scholarship.delete()
    return redirect("dashboard")


@login_required(login_url="signin")
def reg_user(request):
    if not request.user.is_staff:
        return redirect("dashboard")

    users = User.objects.all()
    return render(request, "users.html", {"users": users})


@require_http_methods(["GET", "POST"])
def user_applications(request, user_id):
    if not request.user.is_staff:
        return redirect("dashboard")

    target_user = get_object_or_404(User, id=user_id)
    apps = ScholarshipApplication.objects.filter(applicant=target_user).select_related("scholarship")
    return render(
        request,
        "applications.html",
        {"applications": apps, "user": target_user},
    )


@require_http_methods(["POST"])
def delete_user(request, user_id):
    if not request.user.is_staff:
        return redirect("dashboard")

    target_user = get_object_or_404(User, id=user_id)
    target_user.delete()
    return redirect("reg_users")


def search_scholarship(request):
    scholarships = Scholarship.objects.all()
    search_query = request.GET.get("search_query")
    if search_query:
        scholarships = scholarships.filter(name__icontains=search_query)

    return render(request, "scholarship.html", {"scholarships": scholarships})


def signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        # template uses `mobile`
        mobile_number = request.POST.get("mobile") or request.POST.get("mobile_number")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            return render(request, "signup.html", {"error": "Passwords do not match"})

        user = User.objects.create_user(username=username, email=email, password=password)

        # store mobile_number in a profile-like place is missing in current model.
        # We'll keep it in Web_User table if present; otherwise ignore.
        if mobile_number:
            try:
                from .models import Web_User

                Web_User.objects.update_or_create(user=user, defaults={})
            except Exception:
                pass

        # Optional profile image upload
        try:
            uploaded = request.FILES.get("profile_image")
            if uploaded:
                from .models import WebUserProfile

                profile, _ = WebUserProfile.objects.get_or_create(user=user)
                profile.profile_image = uploaded
                profile.save(update_fields=["profile_image"])
        except Exception:
            # Keep signup working even if upload fails
            pass

        return redirect("dashboard")

    return render(request, "signup.html")



def signin(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if request.POST.get("remember"):
                request.session.set_expiry(60 * 60 * 24 * 30)
            else:
                request.session.set_expiry(0)
            return redirect("dashboard")

        return render(request, "signin.html", {"error": "Invalid username or password"})

    return render(request, "signin.html")


def logout_view(request):
    logout(request)
    return redirect("home")


@login_required(login_url="signin")
def apply_scholarship(request, scholarship_id):
    scholarship = get_object_or_404(Scholarship, id=scholarship_id)

    if request.method == "POST":
        statement = request.POST.get("statement", "")
        app, created = ScholarshipApplication.objects.get_or_create(
            applicant=request.user,
            scholarship=scholarship,
            defaults={"statement": statement, "status": ScholarshipApplication.Status.NEW},
        )
        if not created:
            app.statement = statement
            app.status = ScholarshipApplication.Status.NEW
            app.save()
        return redirect("my_applications")

    return render(request, "apply.html", {"scholarship": scholarship})


@login_required(login_url="signin")
def my_applications(request):
    apps = ScholarshipApplication.objects.filter(applicant=request.user).select_related("scholarship")
    return render(request, "applications.html", {"applications": apps})


@login_required(login_url="signin")
def applications_admin(request):
    if not request.user.is_staff:
        return redirect("dashboard")

    qs = ScholarshipApplication.objects.select_related("applicant", "scholarship")
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)

    return render(request, "applications_admin.html", {"applications": qs, "status": status})


@login_required(login_url="signin")
def set_application_status(request, app_id, status):
    if not request.user.is_staff:
        return redirect("dashboard")

    app_obj = get_object_or_404(ScholarshipApplication, id=app_id)

    if status not in dict(ScholarshipApplication.Status.choices):
        raise Http404("Invalid status")

    app_obj.status = status
    app_obj.save(update_fields=["status", "updated_at"])
    return redirect("applications_admin")


# @login_required(login_url="signin")
# def profile(request):
#     # Ensure the one-to-one profile row exists so templates can safely access it.
#     from .models import WebUserProfile

#     profile_obj, _ = WebUserProfile.objects.get_or_create(user=request.user)

#     if request.method == "POST" and request.POST.get("action") == "update_profile":
#         new_username = (request.POST.get("new_username") or "").strip()
#         new_email = (request.POST.get("new_email") or "").strip()
#         uploaded = request.FILES.get("profile_image")


#         # Basic validation: do not allow empty values.
#         if not new_username:
#             return render(request, "profile.html", {"profile_error": "Username cannot be empty."})
#         if not new_email:
#             return render(request, "profile.html", {"profile_error": "Email cannot be empty."})

#         # Apply updates (password/role are intentionally NOT touched).
#         try:
#             # Username unique on auth.User model.
#             if User.objects.exclude(id=request.user.id).filter(username=new_username).exists():
#                 return render(request, "profile.html", {"profile_error": "Username is already taken."})

#             if User.objects.exclude(id=request.user.id).filter(email=new_email).exists():
#                 return render(request, "profile.html", {"profile_error": "Email is already in use."})

#             request.user.username = new_username
#             request.user.email = new_email
#             request.user.save(update_fields=["username", "email"])

#             if uploaded:
#                 profile_obj.profile_image = uploaded
#                 profile_obj.save(update_fields=["profile_image"])

#             return render(request, "profile.html", {"profile_success": "Profile updated successfully."})
#         except Exception:
#             return render(request, "profile.html", {"profile_error": "Failed to update profile."})

#     return render(request, "profile.html", {})



from django.contrib import messages

from .models import WebUserProfile


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

@login_required(login_url="signin")
def profile(request):
    profile_obj, created = WebUserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":

        new_username = request.POST.get("new_username", "").strip()
        new_email = request.POST.get("new_email", "").strip()
        uploaded = request.FILES.get("profile_image")

        # Validation
        if not new_username:
            messages.error(request, "Username cannot be empty.")
            return redirect("profile")

        if not new_email:
            messages.error(request, "Email cannot be empty.")
            return redirect("profile")

        # Username already exists
        if User.objects.exclude(pk=request.user.pk).filter(username=new_username).exists():
            messages.error(request, "Username is already taken.")
            return redirect("profile")

        # Email already exists
        if User.objects.exclude(pk=request.user.pk).filter(email=new_email).exists():
            messages.error(request, "Email is already in use.")
            return redirect("profile")

        # Update user
        request.user.username = new_username
        request.user.email = new_email
        request.user.save()

        # Update profile image
        if uploaded:
            profile_obj.profile_image = uploaded
            profile_obj.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    return render(request, "profile.html", {
        "profile": profile_obj
    })

@login_required(login_url="signin")
def setting(request):
    return render(request, "setting.html")


@login_required(login_url="signin")
def report(request):
    
    if not request.user.is_staff:
        return redirect("dashboard")

    context = {
        "applications_new": ScholarshipApplication.objects.filter(status=ScholarshipApplication.Status.NEW).count(),
        "applications_approved": ScholarshipApplication.objects.filter(status=ScholarshipApplication.Status.APPROVED).count(),
        "applications_rejected": ScholarshipApplication.objects.filter(status=ScholarshipApplication.Status.REJECTED).count(),
        "applications_waiting": ScholarshipApplication.objects.filter(status=ScholarshipApplication.Status.WAITING_DISBURSEMENT).count(),
        "applications_disbursed": ScholarshipApplication.objects.filter(status=ScholarshipApplication.Status.DISBURSED).count(),
        "schemes_total": Scholarship.objects.count(),
    }
    return render(request, "report.html", context)


@login_required(login_url="signin")
def pages(request):
    return render(request, "pages.html")


from django.conf import settings
from django.core.mail import EmailMessage

from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.contrib.auth.models import User
import random
import hashlib
import smtplib


@require_http_methods(["GET", "POST"])
def forget_password(request):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()

        if not username:
            return render(
                request,
                "forget_password.html",
                {"error": "Username is required."}
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return render(
                request,
                "forget_password.html",
                {"success": "If the account exists, an OTP has been sent."}
            )

        if not user.email:
            return render(
                request,
                "forget_password.html",
                {"error": "No email is associated with this account."}
            )

        # Generate OTP
        otp_plain = "".join(str(random.randint(0, 9)) for _ in range(6))
        otp_hash = hashlib.sha256(otp_plain.encode()).hexdigest()

        PasswordResetOTP.objects.create(
            user=user,
            otp_hash=otp_hash,
            expires_at=timezone.now() + timezone.timedelta(minutes=5),
        )

        try:
            # Use EmailBackend directly to bypass Django's smtp starttls(keyfile=...)
            # call that fails in this environment.
            email = EmailMessage(
                subject="Password Reset OTP",
                body=f"""Hello {user.username},

Your OTP for password reset is:

{otp_plain}

This OTP is valid for 5 minutes.

Do not share this OTP with anyone.
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.send(fail_silently=False)

            print("OTP sent successfully to:", user.email)

        except Exception as e:
            print("Email Error:", e)

            return render(
                request,
                "forget_password.html",
                {"error": f"Email sending failed: {e}"}
            )

        return render(
            request,
            "reset_password_otp.html",
            {
                "username": username,
                "message": "OTP has been sent to your registered email."
            },
        )

    return render(request, "forget_password.html")

from django.contrib.auth.models import User
from django.shortcuts import render
from django.utils import timezone
import hashlib


def reset_password_otp(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        otp = request.POST.get("otp", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if not all([username, otp, new_password, confirm_password]):
            return render(
                request,
                "reset_password_otp.html",
                {
                    "username": username,
                    "error": "All fields are required."
                },
            )

        if new_password != confirm_password:
            return render(
                request,
                "reset_password_otp.html",
                {
                    "username": username,
                    "error": "Passwords do not match."
                },
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return render(
                request,
                "reset_password_otp.html",
                {
                    "error": "Invalid user."
                },
            )

        otp_hash = hashlib.sha256(otp.encode()).hexdigest()

        otp_record = (
            PasswordResetOTP.objects.filter(
                user=user,
                otp_hash=otp_hash,
                is_used=False,
                expires_at__gt=timezone.now(),
            )
            .order_by("-created_at")
            .first()
        )

        if not otp_record:
            return render(
                request,
                "reset_password_otp.html",
                {
                    "username": username,
                    "error": "Invalid or expired OTP."
                },
            )

        user.set_password(new_password)
        user.save()

        otp_record.is_used = True
        otp_record.save()

        return render(
            request,
            "signin.html",
            {
                "success": "Password has been reset successfully. Please login."
            },
        )

    return render(request, "reset_password_otp.html")