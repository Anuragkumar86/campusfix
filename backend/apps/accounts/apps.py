from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"

    def ready(self):
        from django.db.models.signals import post_migrate

        from .services import ensure_role_groups_after_migrate

        post_migrate.connect(ensure_role_groups_after_migrate, dispatch_uid="campusfix_role_groups")
