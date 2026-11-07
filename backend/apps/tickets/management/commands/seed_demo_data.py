"""
Repeatable seed: role groups, sample departments/categories, demo accounts and
a handful of sample tickets driven through the real service layer.
"""
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import Role, User
from apps.departments.models import Category, Department
from apps.tickets import services

DEPARTMENTS = {
    "Electrical Maintenance": ["Electrical fault / lighting", "Laboratory equipment"],
    "IT & Network Services": ["Network / Wi-Fi"],
    "Housekeeping": ["Cleanliness"],
    "Plumbing & Civil": ["Plumbing / water leakage", "Furniture / carpentry"],
}
SLUGS = {"Electrical Maintenance": "electrical", "IT & Network Services": "network", "Housekeeping": "housekeeping", "Plumbing & Civil": "plumbing"}

SAMPLE_TICKETS = [
    ("Tube light not working in Lab 3", "The tube light above the second row of benches keeps flickering and now fails completely.", "Electrical fault / lighting", "Block-A", "2", "Lab 3"),
    ("Wi-Fi drops every few minutes", "The Wi-Fi in the reading hall disconnects every 5-10 minutes during the afternoon.", "Network / Wi-Fi", "Library", "1", "Reading hall"),
    ("Water leaking from washroom tap", "The tap in the ground-floor washroom is leaking continuously and the floor is wet.", "Plumbing / water leakage", "Hostel-1", "0", "Washroom"),
    ("Dustbins overflowing near canteen", "The dustbins outside the canteen have not been cleared for two days.", "Cleanliness", "Canteen", "", "Entrance"),
    ("Broken bench in classroom 204", "Two benches in room 204 have broken legs and are unsafe to sit on.", "Furniture / carpentry", "Block-B", "2", "Room 204"),
]
# a tiny valid 1x1 PNG so the demo ticket with an attachment has a real image
PNG_1X1 = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
           b"\x00\x00\x00\rIDATx\x9cc\xf8\xcf\xc0\xf0\x1f\x00\x05\x00\x01\xff\x89\x99=\x1d\x00\x00\x00\x00IEND\xaeB`\x82")


class Command(BaseCommand):
    help = "Seed role groups, sample departments/categories, demo users and demo tickets (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--password", default=os.environ.get("DEMO_PASSWORD", "CampusFix@123"))
        parser.add_argument("--no-tickets", action="store_true", help="Only seed reference data and accounts.")

    def handle(self, *args, **opts):
        password = opts["password"]
        call_command("setup_roles", verbosity=0)

        departments = {}
        for dept_name, categories in DEPARTMENTS.items():
            dept, _ = Department.objects.get_or_create(name=dept_name, defaults={"description": f"Sample department: {dept_name}"})
            departments[dept_name] = dept
            for cat in categories:
                Category.objects.get_or_create(department=dept, name=cat, defaults={"description": f"Sample category: {cat}"})

        def make_user(email, first, last, role, department=None, superuser=False):
            user = User.objects.filter(email__iexact=email).first()
            if user is None:
                if superuser:
                    user = User.objects.create_superuser(email, password, first_name=first, last_name=last)
                else:
                    user = User.objects.create_user(email, password, first_name=first, last_name=last, role=role, department=department)
            return user

        make_user("admin@campusfix.test", "Asha", "Admin", Role.ADMINISTRATOR, superuser=True)
        managers, staff = {}, {}
        for dept_name, slug in SLUGS.items():
            dept = departments[dept_name]
            managers[dept_name] = make_user(f"manager.{slug}@campusfix.test", "Manager", slug.title(), Role.DEPARTMENT_MANAGER, dept)
            for n in (1, 2):
                staff[(dept_name, n)] = make_user(f"staff.{slug}{n}@campusfix.test", "Staff", f"{slug.title()}{n}", Role.MAINTENANCE_STAFF, dept)
        students = [make_user(f"student{n}@campusfix.test", "Student", str(n), Role.STUDENT) for n in (1, 2, 3)]
        self.stdout.write(self.style.SUCCESS("Accounts ready."))

        if opts["no_tickets"] or User.objects.filter(reported_tickets__isnull=False).exists():
            self.stdout.write("Tickets skipped (already present or --no-tickets).")
            self._print_accounts(password)
            return

        created = []
        for i, (title, desc, cat_name, building, floor, room) in enumerate(SAMPLE_TICKETS):
            category = Category.objects.get(name=cat_name)
            image = SimpleUploadedFile("photo.png", PNG_1X1, content_type="image/png") if i == 0 else None
            created.append(services.create_ticket(
                reporter=students[i % len(students)], category=category, title=title, description=desc,
                building=building, floor=floor, room_or_area=room, image=image))

        # Drive some tickets through the real workflow so dashboards have data.
        t0, t1, t2, t3, _t4 = created
        dept0 = t0.department
        m0 = managers[dept0.name]
        s0 = staff[(dept0.name, 1)]
        services.change_priority(ticket_id=t0.pk, actor=m0, priority="HIGH", note="Safety risk in a lab.")
        services.assign_ticket(ticket_id=t0.pk, actor=m0, assignee_id=s0.pk, note="Please check today.")
        services.change_status(ticket_id=t0.pk, actor=s0, new_status="IN_PROGRESS")
        services.add_comment(ticket_id=t0.pk, actor=s0, message="Replacement tube ordered; fitting this afternoon.")

        m1, s1 = managers[t1.department.name], staff[(t1.department.name, 1)]
        services.assign_ticket(ticket_id=t1.pk, actor=m1, assignee_id=s1.pk)
        services.change_status(ticket_id=t1.pk, actor=s1, new_status="IN_PROGRESS")
        services.change_status(ticket_id=t1.pk, actor=s1, new_status="RESOLVED", note="Replaced faulty access point.")

        m2, s2 = managers[t2.department.name], staff[(t2.department.name, 2)]
        services.change_priority(ticket_id=t2.pk, actor=m2, priority="URGENT")
        services.assign_ticket(ticket_id=t2.pk, actor=m2, assignee_id=s2.pk, note="Urgent - water wastage.")
        _ = t3  # left OPEN and unassigned for the manager queue demo
        self.stdout.write(self.style.SUCCESS(f"Created {len(created)} sample tickets."))
        self._print_accounts(password)

    def _print_accounts(self, password):
        self.stdout.write("\nDemo accounts (password for all: %s)" % password)
        for user in User.objects.filter(email__endswith="@campusfix.test").order_by("role", "email"):
            self.stdout.write(f"  {user.role:<20} {user.email}")
