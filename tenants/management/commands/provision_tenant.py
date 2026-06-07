from django.core.management.base import BaseCommand

from tenants.utils import provision_tenant


class Command(BaseCommand):
    help = "Provision a tenant schema by creating it and running migrations"

    def add_arguments(self, parser):
        parser.add_argument("tenant_id", type=int, help="ID of the Client to provision")

    def handle(self, *args, **options):
        tenant_id = options["tenant_id"]
        self.stdout.write(f"Provisioning tenant {tenant_id}...")
        provision_tenant(tenant_id)
        self.stdout.write(self.style.SUCCESS(f"Tenant {tenant_id} provisioned"))
