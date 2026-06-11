import logging
from os import path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from tenants.models import Client
from tenants.utils import register_tenant_database, unregister_tenant_database

logger = logging.getLogger(__name__)

DEFAULT_DATA_FILES = [
    "user_data.json",
    "employee_info_data.json",
    "base_data.json",
    "work_info_data.json",
]

OPTIONAL_APP_FIXTURES = {
    "attendance": ["attendance_data.json"],
    "leave": ["leave_data.json"],
    "asset": ["asset_data.json"],
    "recruitment": ["recruitment_data.json"],
    "onboarding": ["onboarding_data.json"],
    "offboarding": ["offboarding_data.json"],
    "pms": ["pms_data.json"],
    "payroll": ["payroll_data.json", "payroll_loanaccount_data.json"],
    "project": ["project_data.json"],
}


class Command(BaseCommand):
    help = "Seed tenant schema with demo data fixtures."

    def add_arguments(self, parser):
        parser.add_argument(
            "tenant_id",
            type=int,
            help="ID of the Client tenant to seed demo data into",
        )
        parser.add_argument(
            "--schema-name",
            dest="schema_name",
            help="Optional schema name override instead of tenant lookup",
        )
        parser.add_argument(
            "--include",
            nargs="+",
            dest="include_apps",
            help=(
                "Optional list of app fixture groups to include. "
                "Supported values: attendance leave asset recruitment onboarding "
                "offboarding pms payroll project"
            ),
        )

    def handle(self, *args, **options):
        tenant_id = options["tenant_id"]
        schema_name = options.get("schema_name")
        include_apps = options.get("include_apps") or []

        if schema_name is None:
            try:
                tenant = Client.objects.get(id=tenant_id)
            except Client.DoesNotExist:
                raise CommandError(f"Tenant with id={tenant_id} does not exist")
            schema_name = tenant.schema_name

        alias = register_tenant_database(schema_name)
        self.stdout.write(f"Seeding demo data into tenant schema '{schema_name}' ({alias})...")

        fixture_files = list(DEFAULT_DATA_FILES)
        for app_name, files in OPTIONAL_APP_FIXTURES.items():
            if apps.is_installed(app_name):
                if not include_apps or app_name in include_apps:
                    fixture_files.extend(files)

        load_errors = []
        for fixture_name in fixture_files:
            fixture_path = path.join(settings.BASE_DIR, "load_data", fixture_name)
            self.stdout.write(f"Loading fixture: {fixture_name}")
            try:
                call_command("loaddata", fixture_path, database=alias, verbosity=0)
            except Exception as exc:
                logger.exception("Failed to load fixture %s", fixture_name)
                load_errors.append(str(exc))

        unregister_tenant_database(schema_name)

        if load_errors:
            error_message = "; ".join(load_errors)
            raise CommandError(f"Demo seed finished with errors: {error_message}")

        self.stdout.write(self.style.SUCCESS(
            f"Tenant schema '{schema_name}' seeded successfully with {len(fixture_files)} fixtures."
        ))
