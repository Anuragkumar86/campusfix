from django.test import Client, TestCase
from django.urls import resolve, reverse

from apps.testing import PASSWORD, World, make_ticket


class DemoUrlAndTemplateTests(TestCase):
    def test_urls_resolve_including_re_path(self):
        self.assertEqual(resolve("/demo/").view_name, "django_demo:index")
        match = resolve("/demo/ref/2026/000123/")
        self.assertEqual(match.kwargs, {"year": "2026", "number": "000123"})
        self.assertEqual(reverse("django_demo:building", args=["Library"]), "/demo/building/Library/")

    def test_regex_rejects_malformed_references(self):
        self.assertEqual(self.client.get("/demo/ref/1999/000001/").status_code, 404)
        self.assertEqual(self.client.get("/demo/ref/2026/12/").status_code, 404)

    def test_reference_lookup_finds_real_ticket(self):
        w = World()
        t = make_ticket(w.student, w.category)
        year, number = t.ticket_number.split("-")[1:]
        r = self.client.get(f"/demo/ref/{year}/{number}/")
        self.assertContains(r, "A ticket with this reference exists")

    def test_template_inheritance_variables_loop_condition_empty(self):
        r = self.client.get("/demo/")
        self.assertTemplateUsed(r, "django_demo/index.html")
        self.assertTemplateUsed(r, "django_demo/base.html")
        self.assertContains(r, "Projector Flickering")  # |title filter + loop
        self.assertContains(r, "(urgent)")  # {% if %}
        self.assertContains(r, "No issues in this list")  # {% empty %}
        self.assertContains(r, "no preferred building cookie")

    def test_building_page_loop_and_empty(self):
        self.assertContains(self.client.get("/demo/building/library/"), "Wi-Fi down")
        self.assertContains(self.client.get("/demo/building/Nowhere/"), "No sample issues")


class DemoFormTests(TestCase):
    valid = {"name": "Anurag Kumar", "building": "Block-A", "urgency": 3, "message": "The projector is flickering badly."}

    def test_get_renders_form_with_csrf_token(self):
        self.assertContains(self.client.get("/demo/feedback/"), "csrfmiddlewaretoken")

    def test_invalid_post_shows_field_errors(self):
        r = self.client.post("/demo/feedback/", {"name": "R2D2!", "building": "", "urgency": 9, "message": "short"})
        self.assertEqual(r.status_code, 200)
        form = r.context["form"]
        self.assertEqual(set(form.errors), {"name", "building", "urgency", "message"})

    def test_cross_field_validation(self):
        r = self.client.post("/demo/feedback/", {**self.valid, "urgency": 5, "message": "Ten chars!!"})
        self.assertIn("message", r.context["form"].errors)

    def test_valid_post_redirects_and_records_in_session(self):
        r = self.client.post("/demo/feedback/", self.valid)
        self.assertRedirects(r, "/demo/feedback/done/")  # Post/Redirect/Get
        self.assertEqual(self.client.session["demo_feedback"][0]["name"], "Anurag Kumar")
        self.assertContains(self.client.get("/demo/feedback/done/"), "Anurag Kumar")

    def test_csrf_is_enforced_on_post(self):
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post("/demo/feedback/", self.valid).status_code, 403)


class DemoCookieSessionAuthTests(TestCase):
    def test_session_counter_increments(self):
        self.client.get("/demo/session/")
        r = self.client.get("/demo/session/")
        self.assertContains(r, "<strong>2</strong>")

    def test_cookie_set_read_and_cleared(self):
        r = self.client.post("/demo/cookie/", {"building": "Library"})
        self.assertEqual(self.client.cookies["preferred_building"].value, "Library")
        self.assertTrue(r.cookies["preferred_building"]["httponly"])
        self.assertContains(self.client.get("/demo/"), "Library")
        self.client.post("/demo/cookie/clear/")
        self.assertEqual(self.client.cookies["preferred_building"].value, "")

    def test_invalid_cookie_value_not_stored(self):
        self.client.post("/demo/cookie/", {"building": "<script>"})
        self.assertNotIn("preferred_building", self.client.cookies)

    def test_protected_page_redirects_anonymous_to_login(self):
        self.assertRedirects(self.client.get("/demo/secret/"), "/demo/login/?next=/demo/secret/")

    def test_login_logout_flow(self):
        w = World()
        r = self.client.post("/demo/login/?next=/demo/secret/", {"username": w.student.email, "password": PASSWORD})
        self.assertRedirects(r, "/demo/secret/")
        self.assertContains(self.client.get("/demo/secret/"), "Protected page")
        self.client.post("/demo/logout/")
        self.assertEqual(self.client.get("/demo/secret/").status_code, 302)

    def test_bad_login_stays_on_form(self):
        r = self.client.post("/demo/login/", {"username": "x@example.test", "password": "bad"})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["form"].errors)
