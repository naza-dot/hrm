from django.core.management.base import BaseCommand

from tenants.utils import run_migrations_for_schema


class Command(BaseCommand):
    help = "Run migrations for all active tenant schemas"

    def handle(self, *args, **options):
        from tenants.models import Client

        clients = Client.objects.filter(status="active")
        if not clients.exists():
            self.stdout.write("No active tenants found")
            return

        for client in clients:
            self.stdout.write(f"Migrating schema: {client.schema_name} ({client.name})...")
            run_migrations_for_schema(client.schema_name)
            self.stdout.write(self.style.SUCCESS(f"  Done: {client.name}"))
