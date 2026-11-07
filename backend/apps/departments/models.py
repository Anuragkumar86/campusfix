from django.db import models


class Department(models.Model):
    """Operational department responsible for a group of issues."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(models.Model):
    """Classifies reported issues and maps each one to a responsible department."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    # PROTECT: a department used by categories can only be deactivated, not deleted.
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="categories")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"
        constraints = [
            models.UniqueConstraint(fields=["department", "name"], name="unique_category_name_per_department")
        ]

    def __str__(self):
        return self.name
