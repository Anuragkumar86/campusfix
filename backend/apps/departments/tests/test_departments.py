from django.db import IntegrityError
from django.db.models import ProtectedError
from rest_framework.test import APITestCase

from apps.departments.models import Category
from apps.testing import World, make_category, make_ticket


class DepartmentModelTests(APITestCase):
    def setUp(self):
        self.w = World()

    def test_category_names_unique_within_department(self):
        with self.assertRaises(IntegrityError):
            Category.objects.create(department=self.w.dept, name="Lighting")

    def test_used_category_and_department_cannot_be_deleted(self):
        make_ticket(self.w.student, self.w.category)
        with self.assertRaises(ProtectedError):
            self.w.category.delete()
        with self.assertRaises(ProtectedError):
            self.w.dept.delete()

    def test_user_with_tickets_cannot_be_deleted(self):
        make_ticket(self.w.student, self.w.category)
        with self.assertRaises(ProtectedError):
            self.w.student.delete()

    def test_api_lists_only_active_categories_and_requires_login(self):
        make_category(self.w.dept, "Retired", is_active=False)
        self.assertEqual(self.client.get("/api/categories/").status_code, 401)
        self.client.force_login(self.w.student)
        names = {c["name"] for c in self.client.get("/api/categories/").json()}
        self.assertEqual(names, {"Lighting", "Leaks"})
        depts = {d["name"] for d in self.client.get("/api/departments/").json()}
        self.assertEqual(depts, {"Electrical", "Plumbing"})
