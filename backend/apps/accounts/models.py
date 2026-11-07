from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models


class Role(models.TextChoices):
    STUDENT = "STUDENT", "Student"
    MAINTENANCE_STAFF = "MAINTENANCE_STAFF", "Maintenance Staff"
    DEPARTMENT_MANAGER = "DEPARTMENT_MANAGER", "Department Manager"
    ADMINISTRATOR = "ADMINISTRATOR", "Administrator"


class UserManager(BaseUserManager):
    """Manager for a user model that signs in with an e-mail address."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", Role.STUDENT)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True
        extra_fields["role"] = Role.ADMINISTRATOR
        return self._create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        # e-mail login is case-insensitive
        return self.get(email__iexact=email)


class User(AbstractUser):
    """
    Custom user model (decided before the first migration).

    Login identifier: e-mail address.
    ``role`` is the application-level role; the matching Django Group is kept in
    sync by ``apps.accounts.services.sync_user_group``.
    """

    username = None
    email = models.EmailField("email address", unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    department = models.ForeignKey(
        "departments.Department",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="users",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        ordering = ["first_name", "last_name", "email"]

    def __str__(self):
        return f"{self.display_name} <{self.email}>"

    @property
    def display_name(self) -> str:
        return self.get_full_name().strip() or self.email

    @property
    def is_admin_role(self) -> bool:
        return self.is_superuser or self.role == Role.ADMINISTRATOR

    def clean(self):
        super().clean()
        if self.role in (Role.MAINTENANCE_STAFF, Role.DEPARTMENT_MANAGER) and not self.department_id:
            raise ValidationError({"department": "Maintenance staff and department managers need a department."})

    def save(self, *args, **kwargs):
        from .services import sync_user_group

        self.email = (self.email or "").lower()
        # Only administrators (and superusers) may enter Django Admin.
        self.is_staff = bool(self.is_superuser or self.role == Role.ADMINISTRATOR)
        super().save(*args, **kwargs)
        sync_user_group(self)
