from django.contrib import admin

from .models import Scholarship, ScholarshipApplication, Web_User


@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type_of_scholarship", "grade", "year", "category")
    search_fields = ("name", "type_of_scholarship", "category")


@admin.register(ScholarshipApplication)
class ScholarshipApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "applicant", "scholarship", "status", "applied_at", "updated_at")
    list_filter = ("status", "applied_at")
    search_fields = ("applicant__username", "scholarship__name")


@admin.register(Web_User)
class WebUserAdmin(admin.ModelAdmin):
    list_display = ("id", "user")
    search_fields = ("user__username", "user__email")
