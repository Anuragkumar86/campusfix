from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "role", "department", "is_active")
    list_filter = ("role", "department", "is_active")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("CampusFix role", {"fields": ("role", "department")}),
        ("Status", {"fields": ("is_active", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "first_name", "last_name", "role", "department", "password1", "password2")}),
    )
    readonly_fields = ("last_login", "date_joined")

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        # Users cannot edit their own role/department/permissions.
        if obj is not None and obj.pk == request.user.pk:
            fields += ["role", "department", "is_active", "is_superuser", "groups", "user_permissions"]
        return fields
