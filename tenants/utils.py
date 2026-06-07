import logging
import threading

from django.conf import settings
from django.core.management import call_command
from django.db import connections, DEFAULT_DB_ALIAS

logger = logging.getLogger(__name__)


def get_tenant_apps():
    """Return all installed apps that are not in SHARED_APPS."""
    return [
        app for app in settings.INSTALLED_APPS
        if app not in settings.SHARED_APPS
        and not app.startswith("django.")
    ]


def get_tenant_db_alias(schema_name):
    return f"tenant_{schema_name}"


def create_schema(schema_name):
    """Create a PostgreSQL schema."""
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'
        )


def register_tenant_database(schema_name):
    """Register a temporary database alias pointing to the tenant schema."""
    alias = get_tenant_db_alias(schema_name)
    db_config = settings.DATABASES[DEFAULT_DB_ALIAS].copy()
    db_config["OPTIONS"] = db_config.get("OPTIONS", {}).copy()
    db_config["OPTIONS"]["options"] = f"-c search_path={schema_name},public"
    connections.databases[alias] = db_config
    return alias


def unregister_tenant_database(schema_name):
    alias = get_tenant_db_alias(schema_name)
    connections.databases.pop(alias, None)


def run_migrations_for_schema(schema_name, progress_callback=None):
    """Run Django migrations for all tenant apps in the given schema."""
    tenant_apps = get_tenant_apps()
    alias = register_tenant_database(schema_name)
    try:
        total = len(tenant_apps)
        for i, app in enumerate(tenant_apps):
            logger.info(f"Migrating {app} for schema {schema_name}")
            call_command("migrate", app, database=alias, verbosity=0)
            if progress_callback:
                progress = int(((i + 1) / total) * 100)
                progress_callback(progress)
    finally:
        unregister_tenant_database(schema_name)


def provision_tenant(tenant_id):
    """Provision a tenant by creating its schema and running migrations."""
    from tenants.models import Client

    try:
        tenant = Client.objects.get(id=tenant_id)
    except Client.DoesNotExist:
        logger.error(f"Tenant {tenant_id} not found")
        return

    def update_progress(progress):
        Client.objects.filter(id=tenant_id).update(progress=progress)

    try:
        tenant.status = "creating"
        tenant.progress = 0
        tenant.save(update_fields=["status", "progress"])

        create_schema(tenant.schema_name)
        update_progress(5)

        run_migrations_for_schema(tenant.schema_name, progress_callback=update_progress)

        tenant.status = "active"
        tenant.progress = 100
        tenant.save(update_fields=["status", "progress"])
        logger.info(f"Tenant {tenant.name} provisioned successfully")
    except Exception as e:
        logger.exception(f"Failed to provision tenant {tenant.name}: {e}")
        Client.objects.filter(id=tenant_id).update(status="failed")


def provision_tenant_async(tenant_id):
    thread = threading.Thread(target=provision_tenant, args=(tenant_id,))
    thread.daemon = True
    thread.start()
