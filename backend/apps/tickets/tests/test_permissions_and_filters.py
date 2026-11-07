from rest_framework.test import APITestCase

from apps.accounts.models import Role
from apps.testing import World, make_ticket, make_user
from apps.tickets import services


class ScopeTests(APITestCase):
    def setUp(self):
        self.w = World()
        w = self.w
        self.t1 = make_ticket(w.student, w.category, title="Student one ticket")
        self.t2 = make_ticket(w.student2, w.category, title="Student two ticket")
        self.t3 = make_ticket(w.student, w.other_category, title="Plumbing ticket")
        services.assign_ticket(ticket_id=self.t1.pk, actor=w.manager, assignee_id=w.staff.pk)

    def ids(self, user, query=""):
        self.client.force_login(user)
        r = self.client.get(f"/api/tickets/{query}")
        self.assertEqual(r.status_code, 200, r.content)
        return {t["id"] for t in r.json()["results"]}

    def test_list_scopes(self):
        w = self.w
        self.assertEqual(self.ids(w.student), {self.t1.pk, self.t3.pk})
        self.assertEqual(self.ids(w.student2), {self.t2.pk})
        self.assertEqual(self.ids(w.staff), {self.t1.pk})  # only assigned work
        self.assertEqual(self.ids(w.staff2), set())
        self.assertEqual(self.ids(w.manager), {self.t1.pk, self.t2.pk})  # own department only
        self.assertEqual(self.ids(w.other_manager), {self.t3.pk})
        self.assertEqual(self.ids(w.admin), {self.t1.pk, self.t2.pk, self.t3.pk})

    def test_detail_enforces_same_scope_and_conceals_existence(self):
        w = self.w
        for user, ticket, expected in [
            (w.student, self.t1, 200), (w.student2, self.t1, 404), (w.staff, self.t1, 200),
            (w.staff2, self.t1, 404), (w.manager, self.t1, 200), (w.other_manager, self.t1, 404),
            (w.admin, self.t1, 200), (w.staff, self.t2, 404),
        ]:
            self.client.force_login(user)
            self.assertEqual(self.client.get(f"/api/tickets/{ticket.pk}/").status_code, expected, (user.role, ticket.title))

    def test_sub_resources_respect_scope(self):
        self.client.force_login(self.w.student2)
        for path in ("history/", "comments/", ""):
            self.assertEqual(self.client.get(f"/api/tickets/{self.t1.pk}/{path}").status_code, 404)

    def test_manager_cannot_assign_ticket_in_other_department(self):
        self.client.force_login(self.w.manager)
        r = self.client.post(f"/api/tickets/{self.t3.pk}/assignments/", {"assigned_to": self.w.other_staff.pk}, format="json")
        self.assertEqual(r.status_code, 404)

    def test_student_hidden_from_assignment_notes_and_assignment_list(self):
        self.client.force_login(self.w.manager)
        self.client.post(f"/api/tickets/{self.t2.pk}/assignments/", {"assigned_to": self.w.staff2.pk, "note": "internal instruction"}, format="json")
        self.client.force_login(self.w.student2)
        data = self.client.get(f"/api/tickets/{self.t2.pk}/").json()
        self.assertEqual(data["assignments"], [])
        notes = [h["note"] for h in data["history"] if h["event_type"] == "ASSIGNMENT"]
        self.assertEqual(notes, [""])
        self.client.force_login(self.w.manager)
        data = self.client.get(f"/api/tickets/{self.t2.pk}/").json()
        self.assertEqual(len(data["assignments"]), 1)

    def test_permissions_block_tells_ui_what_is_allowed(self):
        self.client.force_login(self.w.manager)
        p = self.client.get(f"/api/tickets/{self.t2.pk}/").json()["permissions"]
        self.assertTrue(p["can_assign"] and p["can_set_priority"])
        self.client.force_login(self.w.staff)
        p = self.client.get(f"/api/tickets/{self.t1.pk}/").json()["permissions"]
        self.assertFalse(p["can_assign"])
        self.assertEqual(p["available_transitions"], ["IN_PROGRESS"])

    def test_history_cannot_be_modified_through_api(self):
        self.client.force_login(self.w.admin)
        self.assertEqual(self.client.post(f"/api/tickets/{self.t1.pk}/history/", {}, format="json").status_code, 405)

    def test_staff_who_is_also_reporter_sees_own_report(self):
        t = make_ticket(self.w.student, self.w.category)
        t.reporter = self.w.staff2
        t.save()
        self.assertIn(t.pk, self.ids(self.w.staff2))


class FilterTests(APITestCase):
    def setUp(self):
        self.w = World()
        w = self.w
        self.a = make_ticket(w.student, w.category, title="Projector broken", building="Block-A")
        self.b = make_ticket(w.student, w.category, title="Fan noisy", building="Library")
        self.c = make_ticket(w.student, w.category, title="Switch sparks", building="Block-A")
        services.change_priority(ticket_id=self.c.pk, actor=w.manager, priority="URGENT")
        services.change_priority(ticket_id=self.a.pk, actor=w.manager, priority="LOW")
        services.assign_ticket(ticket_id=self.b.pk, actor=w.manager, assignee_id=w.staff.pk)
        self.client.force_login(w.manager)

    def q(self, query):
        r = self.client.get(f"/api/tickets/?{query}")
        self.assertEqual(r.status_code, 200, r.content)
        return [t["id"] for t in r.json()["results"]]

    def test_search_by_ticket_number_and_text(self):
        self.assertEqual(self.q(f"search={self.a.ticket_number}"), [self.a.pk])
        self.assertEqual(self.q("search=projector"), [self.a.pk])

    def test_filter_status_priority_category_building(self):
        self.assertEqual(self.q("status=ASSIGNED"), [self.b.pk])
        self.assertEqual(self.q("priority=URGENT"), [self.c.pk])
        self.assertEqual(set(self.q(f"category={self.w.category.pk}")), {self.a.pk, self.b.pk, self.c.pk})
        self.assertEqual(set(self.q("category=light")), {self.a.pk, self.b.pk, self.c.pk})
        self.assertEqual(set(self.q("building=block-a")), {self.a.pk, self.c.pk})

    def test_unassigned_filter(self):
        self.assertEqual(set(self.q("unassigned=true")), {self.a.pk, self.c.pk})

    def test_invalid_filter_value_returns_400(self):
        self.assertEqual(self.client.get("/api/tickets/?status=NOPE").status_code, 400)
        self.assertEqual(self.client.get("/api/tickets/?created_after=notadate").status_code, 400)

    def test_sorting_by_priority_uses_severity_not_alphabet(self):
        order = self.q("ordering=-priority")
        self.assertEqual(order[0], self.c.pk)  # URGENT first
        self.assertEqual(order[-1], self.a.pk)  # LOW last
        self.assertEqual(self.q("ordering=created_at")[0], self.a.pk)

    def test_pagination(self):
        for i in range(25):
            make_ticket(self.w.student, self.w.category, title=f"Bulk {i}")
        r = self.client.get("/api/tickets/?page_size=10&page=2").json()
        self.assertEqual(r["count"], 28)
        self.assertEqual(len(r["results"]), 10)
        self.assertIsNotNone(r["next"])
        self.assertEqual(len(self.client.get("/api/tickets/").json()["results"]), 20)  # default size

    def test_filters_never_widen_scope(self):
        self.client.force_login(self.w.student2)
        self.assertEqual(self.q("search=Projector"), [])
        self.assertEqual(self.q(f"search={self.a.ticket_number}"), [])
