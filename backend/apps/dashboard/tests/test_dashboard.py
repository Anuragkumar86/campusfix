from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from apps.testing import World, make_ticket
from apps.tickets import services
from apps.tickets.models import Ticket


class DashboardTests(APITestCase):
    def setUp(self):
        self.w = World()

    def get(self, user, path="summary"):
        self.client.force_login(user)
        r = self.client.get(f"/api/dashboard/{path}/")
        self.assertEqual(r.status_code, 200, r.content)
        return r.json()

    def test_empty_data_returns_zeros_not_errors(self):
        s = self.get(self.w.student)
        self.assertEqual((s["total"], s["open_count"], s["recent"]), (0, 0, []))
        m = self.get(self.w.manager)
        self.assertEqual((m["total"], m["unassigned"], m["overdue"], m["avg_resolution_hours"]), (0, 0, 0, None))
        self.assertEqual(sum(m["by_status"].values()), 0)
        st = self.get(self.w.staff)
        self.assertEqual((st["total"], st["overdue"]), (0, 0))
        self.assertEqual(self.get(self.w.manager, "categories"), [])
        self.assertEqual(self.get(self.w.manager, "overdue")["count"], 0)

    def test_student_numbers_match_ticket_list(self):
        w = self.w
        a = make_ticket(w.student, w.category)
        b = make_ticket(w.student, w.category)
        make_ticket(w.student2, w.category)
        services.assign_ticket(ticket_id=b.pk, actor=w.manager, assignee_id=w.staff.pk)
        services.change_status(ticket_id=b.pk, actor=w.staff, new_status="IN_PROGRESS")
        s = self.get(w.student)
        self.assertEqual(s["total"], 2)
        self.assertEqual((s["open_count"], s["in_progress"], s["resolved_or_closed"]), (1, 1, 0))
        self.assertEqual(len(self.client.get("/api/tickets/").json()["results"]), s["total"])

    def test_manager_summary_is_department_scoped_and_consistent(self):
        w = self.w
        t1 = make_ticket(w.student, w.category)
        t2 = make_ticket(w.student, w.category)
        make_ticket(w.student, w.other_category)  # other department
        services.change_priority(ticket_id=t1.pk, actor=w.manager, priority="HIGH")
        services.assign_ticket(ticket_id=t2.pk, actor=w.manager, assignee_id=w.staff.pk)
        m = self.get(w.manager)
        self.assertEqual(m["total"], 2)
        self.assertEqual(m["by_status"]["OPEN"], 1)
        self.assertEqual(m["by_status"]["ASSIGNED"], 1)
        self.assertEqual(m["by_priority"]["HIGH"], 1)
        self.assertEqual(m["unassigned"], 1)
        self.assertEqual(self.client.get("/api/tickets/?unassigned=true").json()["count"], m["unassigned"])
        self.assertEqual(m["department"]["name"], "Electrical")
        cats = self.get(w.manager, "categories")
        self.assertEqual(cats, [{"category_id": w.category.pk, "category": "Lighting", "count": 2}])

    def test_overdue_listing_and_roles(self):
        w = self.w
        late = make_ticket(w.student, w.category)
        ok = make_ticket(w.student, w.category)
        services.assign_ticket(ticket_id=late.pk, actor=w.manager, assignee_id=w.staff.pk)
        Ticket.objects.filter(pk=late.pk).update(resolution_due_at=timezone.now() - timedelta(hours=1))
        data = self.get(w.manager, "overdue")
        self.assertEqual([t["id"] for t in data["results"]], [late.pk])
        self.assertEqual(self.get(w.manager)["overdue"], 1)
        self.assertEqual(self.get(w.staff, "overdue")["count"], 1)  # own assigned work
        self.assertEqual(self.get(w.staff2, "overdue")["count"], 0)
        self.client.force_login(w.student)
        self.assertEqual(self.client.get("/api/dashboard/overdue/").status_code, 403)
        self.assertEqual(self.client.get("/api/dashboard/categories/").status_code, 403)
        self.client.force_login(w.staff)
        self.assertEqual(self.client.get("/api/dashboard/categories/").status_code, 403)

    def test_resolution_time_summary(self):
        w = self.w
        t = make_ticket(w.student, w.category)
        services.assign_ticket(ticket_id=t.pk, actor=w.manager, assignee_id=w.staff.pk)
        services.change_status(ticket_id=t.pk, actor=w.staff, new_status="IN_PROGRESS")
        services.change_status(ticket_id=t.pk, actor=w.staff, new_status="RESOLVED", note="done")
        Ticket.objects.filter(pk=t.pk).update(created_at=timezone.now() - timedelta(hours=10))
        m = self.get(w.manager)
        self.assertEqual(m["resolved_sample_size"], 1)
        self.assertAlmostEqual(m["avg_resolution_hours"], 10.0, delta=0.2)
        self.assertEqual(self.get(w.staff)["recently_completed"][0]["id"], t.pk)

    def test_admin_sees_all_departments(self):
        make_ticket(self.w.student, self.w.category)
        make_ticket(self.w.student, self.w.other_category)
        a = self.get(self.w.admin)
        self.assertEqual(a["total"], 2)
        self.assertEqual({d["name"]: d["tickets_total"] for d in a["by_department"]}, {"Electrical": 1, "Plumbing": 1})
