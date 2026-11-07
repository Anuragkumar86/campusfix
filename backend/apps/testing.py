"""Small factory helpers shared by the test suites."""
import io
import itertools

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.accounts.models import Role, User
from apps.departments.models import Category, Department
from apps.tickets import services

_counter = itertools.count(1)
PASSWORD = "Str0ng!Pass-for-tests"


def make_department(name=None, **kw):
    return Department.objects.create(name=name or f"Dept {next(_counter)}", **kw)


def make_category(department, name=None, **kw):
    return Category.objects.create(department=department, name=name or f"Cat {next(_counter)}", **kw)


def make_user(role=Role.STUDENT, department=None, email=None, **kw):
    n = next(_counter)
    return User.objects.create_user(
        email or f"user{n}@example.test", PASSWORD, first_name="User", last_name=str(n), role=role, department=department, **kw
    )


def make_ticket(reporter, category, **kw):
    data = dict(title="Broken light", description="The light is broken.", building="Block-A")
    data.update(kw)
    return services.create_ticket(reporter=reporter, category=category, **data)


def image_file(fmt="PNG", name="photo.png", size=(4, 4)):
    buf = io.BytesIO()
    Image.new("RGB", size, "red").save(buf, format=fmt)
    return SimpleUploadedFile(name, buf.getvalue(), content_type=f"image/{fmt.lower()}")


class World:
    """A ready-made scenario: two departments, managers, staff, students."""

    def __init__(self):
        self.dept = make_department("Electrical")
        self.other_dept = make_department("Plumbing")
        self.category = make_category(self.dept, "Lighting")
        self.other_category = make_category(self.other_dept, "Leaks")
        self.student = make_user(Role.STUDENT)
        self.student2 = make_user(Role.STUDENT)
        self.manager = make_user(Role.DEPARTMENT_MANAGER, self.dept)
        self.other_manager = make_user(Role.DEPARTMENT_MANAGER, self.other_dept)
        self.staff = make_user(Role.MAINTENANCE_STAFF, self.dept)
        self.staff2 = make_user(Role.MAINTENANCE_STAFF, self.dept)
        self.other_staff = make_user(Role.MAINTENANCE_STAFF, self.other_dept)
        self.admin = make_user(Role.ADMINISTRATOR)
