from django.test import override_settings
from rest_framework.test import APIClient, APITestCase

from apps.testing import PASSWORD, World


class AuthApiTests(APITestCase):
    def setUp(self):
        self.w = World()

    def csrf_client(self):
        client = APIClient(enforce_csrf_checks=True)
        token = client.get("/api/auth/csrf/").json()["csrfToken"]
        return client, token

    def login(self, client, token, email, password=PASSWORD):
        return client.post("/api/auth/login/", {"email": email, "password": password}, format="json", HTTP_X_CSRFTOKEN=token)

    def test_anonymous_gets_401_on_protected_endpoints(self):
        for url in ("/api/auth/me/", "/api/tickets/", "/api/dashboard/summary/", "/api/categories/"):
            self.assertEqual(self.client.get(url).status_code, 401, url)

    def test_login_me_logout_cycle_with_csrf(self):
        client, token = self.csrf_client()
        r = self.login(client, token, self.w.student.email)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["role"], "STUDENT")
        me = client.get("/api/auth/me/")
        self.assertEqual(me.json()["email"], self.w.student.email)
        token = client.get("/api/auth/csrf/").json()["csrfToken"]
        self.assertEqual(client.post("/api/auth/logout/", HTTP_X_CSRFTOKEN=token).status_code, 204)
        self.assertEqual(client.get("/api/auth/me/").status_code, 401)  # session invalidated

    def test_session_cookie_is_httponly(self):
        client, token = self.csrf_client()
        r = self.login(client, token, self.w.student.email)
        self.assertTrue(r.cookies["sessionid"]["httponly"])

    def test_login_without_csrf_token_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        r = client.post("/api/auth/login/", {"email": self.w.student.email, "password": PASSWORD}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_logout_without_csrf_token_is_rejected_and_session_survives(self):
        client, token = self.csrf_client()
        self.login(client, token, self.w.student.email)
        self.assertEqual(client.post("/api/auth/logout/").status_code, 403)
        self.assertEqual(client.get("/api/auth/me/").status_code, 200)

    def test_unsafe_api_request_without_csrf_fails_but_works_with_token(self):
        client, token = self.csrf_client()
        self.login(client, token, self.w.student.email)
        payload = {"title": "T", "description": "D", "category": self.w.category.id, "building": "B"}
        self.assertEqual(client.post("/api/tickets/", payload, format="json").status_code, 403)
        token = client.get("/api/auth/csrf/").json()["csrfToken"]
        self.assertEqual(client.post("/api/tickets/", payload, format="json", HTTP_X_CSRFTOKEN=token).status_code, 201)

    def test_invalid_credentials_message_is_identical_for_unknown_and_wrong_password(self):
        client, token = self.csrf_client()
        a = self.login(client, token, "nobody@example.test", "whatever")
        b = self.login(client, token, self.w.student.email, "wrong-password")
        self.assertEqual(a.status_code, 400)
        self.assertEqual(a.json(), b.json())

    def test_inactive_account_cannot_log_in_and_gets_same_message(self):
        self.w.student.is_active = False
        self.w.student.save()
        client, token = self.csrf_client()
        r = self.login(client, token, self.w.student.email)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json(), {"detail": "Invalid email or password."})

    def test_email_login_is_case_insensitive(self):
        client, token = self.csrf_client()
        self.assertEqual(self.login(client, token, self.w.student.email.upper()).status_code, 200)

    def test_session_expiry(self):
        self.client.force_login(self.w.student)
        # simulate expiry by deleting the server-side session
        from django.contrib.sessions.models import Session
        Session.objects.all().delete()
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_unknown_api_route_returns_json_404(self):
        r = self.client.get("/api/nope/")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r["Content-Type"], "application/json")

    def test_cors_allows_only_configured_origin(self):
        ok = self.client.get("/api/health/", HTTP_ORIGIN="http://localhost:3000")
        self.assertEqual(ok["Access-Control-Allow-Origin"], "http://localhost:3000")
        self.assertEqual(ok["Access-Control-Allow-Credentials"], "true")
        bad = self.client.get("/api/health/", HTTP_ORIGIN="http://evil.example")
        self.assertNotIn("Access-Control-Allow-Origin", bad)

    def test_eligible_staff_endpoint_scopes_by_role(self):
        self.client.force_login(self.w.manager)
        ids = {s["id"] for s in self.client.get("/api/staff/eligible/").json()}
        self.assertEqual(ids, {self.w.staff.id, self.w.staff2.id})
        self.client.force_login(self.w.student)
        self.assertEqual(self.client.get("/api/staff/eligible/").status_code, 403)
        self.client.force_login(self.w.admin)
        ids = {s["id"] for s in self.client.get(f"/api/staff/eligible/?department={self.w.other_dept.id}").json()}
        self.assertEqual(ids, {self.w.other_staff.id})
