"""
URL configuration for scholarshipmanagement project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from scholar import views

urlpatterns = [

    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("signin/", views.signin, name="signin"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),

    path("add_scholarship/", views.add_scholarship, name="add_scholarship"),
    path("delete_scholarship/<int:id>/", views.delete_scholarship, name="delete_scholarship"),
    path("search_scholarship/", views.search_scholarship, name="search_scholarship"),
    path("reg_user/", views.reg_user, name="reg_users"),

    # Registered users actions
    path("users/<int:user_id>/applications/", views.user_applications, name="user_applications"),
    path("users/<int:user_id>/delete/", views.delete_user, name="delete_user"),

    path("pages/", views.pages, name="pages"),
    # Applications
    path("apply/<int:scholarship_id>/", views.apply_scholarship, name="apply_scholarship"),
    path("my-applications/", views.my_applications, name="my_applications"),
    path("admin-applications/", views.applications_admin, name="applications_admin"),
    path(
        "admin-applications/<int:app_id>/set-status/<str:status>/",
        views.set_application_status,
        name="set_application_status",
    ),

    # Profile / Settings / Report
    path("profile/", views.profile, name="profile"),
    path("setting/", views.setting, name="setting"),
    path("report/", views.report, name="report"),

    # Forget password (OTP)
    path("forget-password/", views.forget_password, name="forget_password"),
     path("reset-password-otp/", views.reset_password_otp, name="reset_password_otp"),

    path("admin/", admin.site.urls),
]

# Serve uploaded media during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




