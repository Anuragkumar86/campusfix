from django.core.management.base import BaseCommand

from apps.accounts.services import ensure_role_groups


class Command(BaseCommand):
    help = "Create the four role groups and assign their permissions (safe to run repeatedly)."

    def handle(self, *args, **options):
        ensure_role_groups()
        self.stdout.write(self.style.SUCCESS("Role groups and permissions are up to date."))
