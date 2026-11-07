import threading
from datetime import timedelta

from django.db import IntegrityError, connection, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import Role
from apps.testing import World, image_file, make_ticket, make_user
from apps.tickets.models import Assignment, Ticket, TicketHistory

TEST_SLA = {
    "LOW": {"response_hours": 10, "resolution_hours": 100},
    "MEDIUM": {"response_hours": 2, "resolution_hours": 20},
    "HIGH": {"response_hours": 1, "resolution_hours": 10},
    "URGENT": {"response_hours": 1, "resolution_hours": 2},
}


class ModelTests(TestCase):
    def setUp(self):
        self.w = World()

    def test_ticket_number_format_unique_and_initial_values(self):
        t1 = make_ticket(self.w.student, self.w.category)
        t2 = make_ticket(self.w.student, self.w.category)
        self.assertRegex(t1.ticket_number, r"^CF-\d{4}-\d{6}$")
        self.assertNotEqual(t1.ticket_number, t2.ticket_number)
        t1.refresh_from_db()
        self.assertEqual((t1.status, t1.priority), ("OPEN", "MEDIUM"))
        self.assertEqual(t1.department, self.w.dept)  # derived from the category

    def test_duplicate_ticket_number_rejected_by_database(self):
        t1 = make_ticket(self.w.student, self.w.category)
        t2 = make_ticket(self.w.student, self.w.category)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Ticket.objects.filter(pk=t2.pk).update(ticket_number=t1.ticket_number)

    def test_only_one_active_assignment_per_ticket(self):
        t = make_ticket(self.w.student, self.w.category)
        Assignment.objects.create(ticket=t, assigned_to=self.w.staff, assigned_by=self.w.manager)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Assignment.objects.create(ticket=t, assigned_to=self.w.staff2, assigned_by=self.w.manager)

    def test_history_is_append_only(self):
        t = make_ticket(self.w.student, self.w.category)
        h = t.history.first()
        h.note = "tampered"
        with self.assertRaises(ValueError):
            h.save()

    def test_invalid_status_choice_fails_validation(self):
        from django.core.exceptions import ValidationError
        t = make_ticket(self.w.student, self.w.category)
        t.status = "NOPE"
        with self.assertRaises(ValidationError):
            t.full_clean()


class WorkflowApiTests(APITestCase):
    def setUp(self):
        self.w = World()
        self.t = make_ticket(self.w.student, self.w.category)

    def post(self, user, path, data=None, fmt="json"):
        self.client.force_login(user)
        return self.client.post(f"/api/tickets/{self.t.pk}/{path}/", data or {}, format=fmt)

    def assign(self, staff=None, user=None):
        return self.post(user or self.w.manager, "assignments", {"assigned_to": (staff or self.w.staff).pk, "note": "please fix"})

    def status(self, user, new, note=""):
        return self.post(user, "status", {"status": new, "note": note})

    # --- creation
    def test_student_creates_ticket(self):
        self.client.force_login(self.w.student)
        r = self.client.post("/api/tickets/", {"title": " Fan noise ", "description": "Loud fan", "category": self.w.category.pk, "building": "B1", "reporter": self.w.student2.pk, "status": "CLOSED"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        body = r.json()
        self.assertTrue(body["ticket_number"].startswith("CF-"))
        self.assertEqual(body["title"], "Fan noise")  # trimmed
        self.assertEqual((body["status"], body["priority"]), ("OPEN", "MEDIUM"))
        self.assertEqual(body["reporter"]["id"], self.w.student.pk)  # client-supplied reporter/status ignored
        self.assertEqual(Ticket.objects.get(pk=body["id"]).history.first().event_type, "CREATED")

    def test_missing_fields_rejected_with_field_errors(self):
        self.client.force_login(self.w.student)
        r = self.client.post("/api/tickets/", {"title": "  ", "description": "", "building": ""}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertTrue({"title", "description", "category", "building"} <= set(r.json()))
        self.assertEqual(Ticket.objects.count(), 1)  # nothing created

    def test_inactive_category_rejected(self):
        self.w.category.is_active = False
        self.w.category.save()
        self.client.force_login(self.w.student)
        r = self.client.post("/api/tickets/", {"title": "T", "description": "D", "category": self.w.category.pk, "building": "B"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_staff_and_manager_cannot_create_tickets(self):
        for u in (self.w.staff, self.w.manager):
            self.client.force_login(u)
            r = self.client.post("/api/tickets/", {"title": "T", "description": "D", "category": self.w.category.pk, "building": "B"}, format="json")
            self.assertEqual(r.status_code, 403)

    # --- assignment
    def test_manager_assigns_eligible_staff(self):
        r = self.assign()
        self.assertEqual(r.status_code, 201, r.content)
        self.t.refresh_from_db()
        self.assertEqual(self.t.status, "ASSIGNED")
        self.assertEqual(self.t.current_assignment.assigned_to, self.w.staff)
        self.assertIsNotNone(self.t.first_response_at)
        events = list(self.t.history.values_list("event_type", flat=True))
        self.assertIn("ASSIGNMENT", events)
        self.assertEqual(events.count("STATUS"), 1)

    def test_assignment_rejects_cross_department_inactive_and_non_staff(self):
        self.assertEqual(self.assign(self.w.other_staff).status_code, 400)
        self.w.staff2.is_active = False
        self.w.staff2.save()
        self.assertEqual(self.assign(self.w.staff2).status_code, 400)
        self.assertEqual(self.assign(self.w.student).status_code, 400)
        self.assertEqual(self.t.assignments.count(), 0)
        self.t.refresh_from_db()
        self.assertEqual(self.t.status, "OPEN")  # no partial change

    def test_reassignment_preserves_previous_record(self):
        self.assign(self.w.staff)
        r = self.assign(self.w.staff2)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.t.assignments.count(), 2)
        self.assertEqual(self.t.assignments.filter(is_active=True).count(), 1)
        old = self.t.assignments.get(assigned_to=self.w.staff)
        self.assertFalse(old.is_active)
        self.assertIsNotNone(old.unassigned_at)

    def test_assigning_same_staff_again_conflicts(self):
        self.assign()
        self.assertEqual(self.assign().status_code, 409)

    def test_wrong_roles_cannot_assign(self):
        for u in (self.w.student, self.w.staff, self.w.other_manager):
            r = self.assign(user=u)
            self.assertIn(r.status_code, (403, 404), u.role)
        self.assertEqual(self.t.assignments.count(), 0)

    def test_admin_can_assign(self):
        self.assertEqual(self.assign(user=self.w.admin).status_code, 201)

    # --- status workflow
    def full_cycle_to_resolved(self):
        self.assign()
        self.assertEqual(self.status(self.w.staff, "IN_PROGRESS").status_code, 200)
        return self.status(self.w.staff, "RESOLVED", "Replaced the bulb")

    def test_full_happy_path(self):
        self.assertEqual(self.full_cycle_to_resolved().status_code, 200)
        self.t.refresh_from_db()
        self.assertEqual(self.t.status, "RESOLVED")
        self.assertEqual(self.t.resolution_note, "Replaced the bulb")
        self.assertIsNotNone(self.t.resolved_at)
        self.assertEqual(self.status(self.w.student, "CLOSED").status_code, 200)
        self.t.refresh_from_db()
        self.assertEqual(self.t.status, "CLOSED")
        trail = [(h.old_value, h.new_value) for h in self.t.history.filter(event_type="STATUS")]
        self.assertEqual(trail, [("OPEN", "ASSIGNED"), ("ASSIGNED", "IN_PROGRESS"), ("IN_PROGRESS", "RESOLVED"), ("RESOLVED", "CLOSED")])

    def test_invalid_transition_returns_409(self):
        self.assertEqual(self.status(self.w.manager, "CLOSED").status_code, 409)
        self.assertEqual(self.status(self.w.manager, "IN_PROGRESS").status_code, 409)
        self.assertEqual(self.status(self.w.manager, "ASSIGNED").status_code, 409)  # must use assignment endpoint
        self.assertEqual(self.status(self.w.manager, "BOGUS").status_code, 400)

    def test_resolution_requires_note(self):
        self.assign()
        self.status(self.w.staff, "IN_PROGRESS")
        r = self.status(self.w.staff, "RESOLVED", "   ")
        self.assertEqual(r.status_code, 400)
        self.t.refresh_from_db()
        self.assertEqual(self.t.status, "IN_PROGRESS")

    def test_reopen_requires_reason_and_restarts_sla(self):
        self.full_cycle_to_resolved()
        self.assertEqual(self.status(self.w.student, "REOPENED", "").status_code, 400)
        r = self.status(self.w.student, "REOPENED", "Still flickering")
        self.assertEqual(r.status_code, 200)
        self.t.refresh_from_db()
        self.assertEqual(self.t.status, "REOPENED")
        self.assertIsNone(self.t.resolved_at)
        self.assertIsNone(self.t.first_response_at)
        self.assertEqual(self.assign(self.w.staff2).status_code, 201)  # REOPENED -> ASSIGNED
        self.t.refresh_from_db()
        self.assertEqual(self.t.status, "ASSIGNED")

    def test_closed_can_only_be_reopened_by_manager_or_admin(self):
        self.full_cycle_to_resolved()
        self.status(self.w.student, "CLOSED")
        self.assertEqual(self.status(self.w.student, "REOPENED", "reason").status_code, 403)
        self.assertEqual(self.status(self.w.manager, "REOPENED", "reason").status_code, 200)

    def test_student_cannot_resolve_or_start_work(self):
        self.assign()
        self.assertEqual(self.status(self.w.student, "IN_PROGRESS").status_code, 403)
        self.status(self.w.staff, "IN_PROGRESS")
        self.assertEqual(self.status(self.w.student, "RESOLVED", "done").status_code, 403)
        self.t.refresh_from_db()
        self.assertEqual(self.t.status, "IN_PROGRESS")

    def test_staff_cannot_update_ticket_not_assigned_to_them(self):
        self.assign(self.w.staff)
        r = self.status(self.w.staff2, "IN_PROGRESS")
        self.assertEqual(r.status_code, 404)  # outside their scope: existence is concealed

    def test_unassign_from_assigned_returns_to_open(self):
        self.assign()
        r = self.status(self.w.manager, "OPEN", "Wrong team")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.t.assignments.filter(is_active=True).count(), 0)

    def test_status_cannot_be_changed_by_patch(self):
        self.client.force_login(self.w.student)
        r = self.client.patch(f"/api/tickets/{self.t.pk}/", {"status": "CLOSED", "priority": "URGENT", "title": "Edited"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.t.refresh_from_db()
        self.assertEqual((self.t.status, self.t.priority, self.t.title), ("OPEN", "MEDIUM", "Edited"))

    def test_put_and_delete_not_allowed(self):
        self.client.force_login(self.w.admin)
        self.assertEqual(self.client.put(f"/api/tickets/{self.t.pk}/", {}, format="json").status_code, 405)
        self.assertEqual(self.client.delete(f"/api/tickets/{self.t.pk}/").status_code, 405)

    # --- priority & SLA
    def test_priority_change_by_manager_recalculates_deadlines_and_records_history(self):
        before = Ticket.objects.get(pk=self.t.pk).resolution_due_at
        r = self.post(self.w.manager, "priority", {"priority": "URGENT", "note": "safety"})
        self.assertEqual(r.status_code, 200, r.content)
        self.t.refresh_from_db()
        self.assertEqual(self.t.priority, "URGENT")
        self.assertLess(self.t.resolution_due_at, before)
        events = list(self.t.history.values_list("event_type", flat=True))
        self.assertIn("PRIORITY", events)
        self.assertIn("DEADLINE", events)

    def test_priority_change_forbidden_for_student_and_staff_and_other_manager(self):
        self.assign()
        for u in (self.w.student, self.w.staff, self.w.other_manager):
            self.assertIn(self.post(u, "priority", {"priority": "HIGH"}).status_code, (403, 404))
        self.t.refresh_from_db()
        self.assertEqual(self.t.priority, "MEDIUM")

    @override_settings(SLA_TARGETS=TEST_SLA)
    def test_sla_deadlines_use_configured_targets_and_overdue_boundaries(self):
        t = make_ticket(self.w.student, self.w.category)
        self.assertEqual(t.resolution_due_at - t.sla_started_at, timedelta(hours=20))
        self.assertFalse(t.is_overdue)
        Ticket.objects.filter(pk=t.pk).update(resolution_due_at=timezone.now() - timedelta(seconds=1))
        t.refresh_from_db()
        self.assertTrue(t.is_overdue)
        self.assertIn(t, Ticket.objects.overdue())
        Ticket.objects.filter(pk=t.pk).update(status="RESOLVED")  # resolved is never "active overdue"
        t.refresh_from_db()
        self.assertFalse(t.is_overdue)
        self.assertNotIn(t, Ticket.objects.overdue())

    def test_missed_response_deadline_counts_as_overdue_until_first_response(self):
        Ticket.objects.filter(pk=self.t.pk).update(response_due_at=timezone.now() - timedelta(minutes=1))
        self.t.refresh_from_db()
        self.assertTrue(self.t.is_overdue)
        self.assign()
        self.t.refresh_from_db()
        self.assertFalse(self.t.is_overdue)

    # --- comments
    def test_comment_rules(self):
        self.assign()
        post = lambda u, m: self.post(u, "comments", {"message": m})
        self.assertEqual(post(self.w.student, "Any update?").status_code, 201)
        self.assertEqual(post(self.w.staff, "On it").status_code, 201)
        self.assertEqual(post(self.w.manager, "Noted").status_code, 201)
        self.assertEqual(post(self.w.student, "   ").status_code, 400)
        self.assertEqual(post(self.w.student2, "intruder").status_code, 404)
        self.assertEqual(post(self.w.staff2, "intruder").status_code, 404)
        self.client.force_login(self.w.student)
        authors = [c["author"]["id"] for c in self.client.get(f"/api/tickets/{self.t.pk}/comments/").json()]
        self.assertEqual(authors, [self.w.student.pk, self.w.staff.pk, self.w.manager.pk])  # chronological


class TransactionAndConcurrencyTests(TransactionTestCase):
    def test_failed_assignment_leaves_no_partial_history(self):
        w = World()
        t = make_ticket(w.student, w.category)
        from apps.tickets import services
        from rest_framework.exceptions import ValidationError
        before = TicketHistory.objects.count()
        with self.assertRaises(ValidationError):
            services.assign_ticket(ticket_id=t.pk, actor=w.manager, assignee_id=w.other_staff.pk)
        self.assertEqual(TicketHistory.objects.count(), before)
        t.refresh_from_db()
        self.assertEqual(t.status, "OPEN")

    def test_concurrent_assignments_leave_exactly_one_active(self):
        w = World()
        t = make_ticket(w.student, w.category)
        from apps.tickets import services
        results = []

        def run(staff):
            try:
                services.assign_ticket(ticket_id=t.pk, actor=w.manager, assignee_id=staff.pk)
                results.append("ok")
            except Exception as exc:  # noqa: BLE001
                results.append(type(exc).__name__)
            finally:
                connection.close()

        threads = [threading.Thread(target=run, args=(s,)) for s in (w.staff, w.staff2)]
        [th.start() for th in threads]
        [th.join() for th in threads]
        self.assertEqual(Assignment.objects.filter(ticket=t, is_active=True).count(), 1)
        self.assertEqual(results.count("ok"), 2)  # the second one reassigns after the first commits
        self.assertEqual(Assignment.objects.filter(ticket=t).count(), 2)
