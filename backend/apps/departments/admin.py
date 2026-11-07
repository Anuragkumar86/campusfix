from django.contrib import admin

from .models import Category, Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "is_active")
    list_filter = ("is_active", "department")
    search_fields = ("name", "description")
