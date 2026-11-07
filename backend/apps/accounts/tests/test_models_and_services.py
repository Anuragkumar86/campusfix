from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.accounts.models import Role, User
from apps.accounts.services import ROLE_GROUPS, change_user_role
from apps.testing import World, make_department, make_user


class UserModelTests(TestCase):
    def test_email_is_login_identifier_and_unique_case_insensitively(self):
        User.objects.create_user("A@Example.test", "x")
        self.assertTrue(User.objects.filter(email="a@example.test").exists())
        with self.assertRaises(IntegrityError):
            User.objects.create_user("a@example.test", "y")

    def test_get_by_natural_key_is_case_insensitive(self):
        user = make_user(email="case@example.test")
        self.assertEqual(User.objects.get_by_natural_key("CASE@example.test"), user)

    def test_role_department_relationship(self):
        dept = make_department("Electrical")
        manager = make_user(Role.DEPARTMENT_MANAGER, dept)
        self.assertEqual(manager.department, dept)
        self.assertIn(manager, dept.users.all())

    def test_staff_without_department_fails_validation(self):
        user = User(email="s@example.test", role=Role.MAINTENANCE_STAFF)
        with self.assertRaises(ValidationError):
            user.clean()

    def test_password_is_hashed(self):
        user = make_user()
        self.assertNotIn("Str0ng", user.password)
        self.assertTrue(user.check_password("Str0ng!Pass-for-tests"))

    def test_only_administrators_get_django_admin_access(self):
        w = World()
        self.assertTrue(w.admin.is_staff)
        for u in (w.student, w.manager, w.staff):
            self.assertFalse(u.is_staff)

    def test_create_superuser_is_administrator_role(self):
        su = User.objects.create_superuser("root@example.test", "pw")
        self.assertEqual(su.role, Role.ADMINISTRATOR)
        self.assertTrue(su.is_superuser)


class GroupSyncTests(TestCase):
    def role_groups(self, user):
        return set(user.groups.filter(name__in=ROLE_GROUPS.values()).values_list("name", flat=True))

    def test_four_role_groups_exist(self):
        self.assertEqual(set(Group.objects.filter(name__in=ROLE_GROUPS.values()).values_list("name", flat=True)), set(ROLE_GROUPS.values()))

    def test_new_user_joins_matching_group(self):
        self.assertEqual(self.role_groups(make_user(Role.STUDENT)), {"STUDENT"})

    def test_role_change_moves_group_membership(self):
        w = World()
        change_user_role(actor=w.admin, target=w.student, role=Role.MAINTENANCE_STAFF, department=w.dept)
        w.student.refresh_from_db()
        self.assertEqual(self.role_groups(w.student), {"MAINTENANCE_STAFF"})

    def test_user_cannot_change_own_role(self):
        w = World()
        with self.assertRaises(PermissionDenied):
            change_user_role(actor=w.admin, target=w.admin, role=Role.STUDENT)

    def test_non_admin_cannot_change_roles(self):
        w = World()
        with self.assertRaises(PermissionDenied):
            change_user_role(actor=w.manager, target=w.student, role=Role.ADMINISTRATOR)

    def test_group_permissions_differ_by_role(self):
        w = World()
        self.assertTrue(w.student.has_perm("tickets.add_ticket"))
        self.assertFalse(w.student.has_perm("tickets.add_assignment"))
        self.assertTrue(w.manager.has_perm("tickets.add_assignment"))
        self.assertFalse(w.staff.has_perm("tickets.add_assignment"))
        self.assertTrue(w.admin.has_perm("accounts.change_user"))
