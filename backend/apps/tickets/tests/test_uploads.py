import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.testing import World, image_file, make_ticket
from apps.tickets.models import Attachment

TMP = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TMP, MAX_UPLOAD_SIZE=50_000)
class UploadTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP, ignore_errors=True)

    def setUp(self):
        self.w = World()
        self.t = make_ticket(self.w.student, self.w.category)

    def create(self, upload):
        self.client.force_login(self.w.student)
        return self.client.post("/api/tickets/", {"title": "T", "description": "D", "category": self.w.category.pk, "building": "B", "image": upload}, format="multipart")

    def test_valid_image_on_create_is_stored_with_metadata(self):
        r = self.create(image_file())
        self.assertEqual(r.status_code, 201, r.content)
        att = Attachment.objects.get(ticket_id=r.json()["id"])
        self.assertEqual(att.uploaded_by, self.w.student)
        self.assertEqual(att.content_type, "image/png")
        self.assertTrue(att.file.name.endswith(".png"))
        self.assertNotIn("photo", att.file.name)  # generated storage key, not the user's filename
        self.assertEqual(len(r.json()["attachments"]), 1)

    def test_non_image_with_image_extension_rejected(self):
        fake = SimpleUploadedFile("evil.png", b"<?php echo 1; ?>", content_type="image/png")
        r = self.create(fake)
        self.assertEqual(r.status_code, 400)
        self.assertIn("image", r.json())
        self.assertEqual(Attachment.objects.count(), 0)

    def test_unsupported_image_format_rejected(self):
        self.assertEqual(self.create(image_file("BMP", "x.bmp")).status_code, 400)

    def test_oversized_file_rejected(self):
        big = SimpleUploadedFile("big.png", b"0" * 60_000, content_type="image/png")
        self.assertEqual(self.create(big).status_code, 400)

    def test_failed_validation_creates_no_ticket(self):
        count = self.t.__class__.objects.count()
        self.create(SimpleUploadedFile("evil.png", b"nope", content_type="image/png"))
        self.assertEqual(self.t.__class__.objects.count(), count)

    def test_add_attachment_later_and_download_permissions(self):
        self.client.force_login(self.w.student)
        r = self.client.post(f"/api/tickets/{self.t.pk}/attachments/", {"file": image_file("JPEG", "a.jpg")}, format="multipart")
        self.assertEqual(r.status_code, 201, r.content)
        url = r.json()["url"]
        ok = self.client.get(url)
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok["Content-Type"], "image/jpeg")
        self.assertEqual(ok["X-Content-Type-Options"], "nosniff")
        self.client.force_login(self.w.student2)
        self.assertEqual(self.client.get(url).status_code, 404)  # unauthorized download denied
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 401)
        self.client.force_login(self.w.manager)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_upload_by_unrelated_user_denied(self):
        self.client.force_login(self.w.student2)
        r = self.client.post(f"/api/tickets/{self.t.pk}/attachments/", {"file": image_file()}, format="multipart")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(Attachment.objects.count(), 0)
