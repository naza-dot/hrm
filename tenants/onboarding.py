from django_tenants.utils import schema_context
from django.contrib.auth import get_user_model
from .models import Client, Domain


def provision_new_tenant(
    company_name,
    domain,
    schema_name,
    features,
    admin_email,
    admin_password,
    paid_until=None,
    max_employees=None,
):
    tenant = Client.objects.create(
        schema_name=schema_name,
        name=company_name,
        features=features,
        paid_until=paid_until,
        max_employees=max_employees,
        is_active=True,
    )

    Domain.objects.create(
        domain=domain,
        tenant=tenant,
        is_primary=True,
    )

    from django.core.management import call_command
    from io import StringIO
    out = StringIO()
    call_command("migrate_schemas", schema_name=schema_name, stdout=out)
    print(out.getvalue())

    with schema_context(schema_name):
        User = get_user_model()
        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(
                username="admin",
                email=admin_email,
                password=admin_password,
            )

    return tenant
