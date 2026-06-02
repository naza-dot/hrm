#!/bin/bash

echo "Waiting for database to be ready..."
python3 manage.py migrate_schemas --shared

# Create public tenant BEFORE running tenant migrations
python3 -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()
from tenants.models import Client, Domain
if not Client.objects.filter(schema_name='public').exists():
    t = Client(schema_name='public', name='Platform', is_active=True, features={})
    t.save(verbosity=0)
    Domain.objects.create(domain='localhost', tenant=t, is_primary=True)
    print('Public tenant created')
else:
    print('Public tenant already exists')
"

# Now run tenant migrations (creates tenant app tables in tenant schemas)
python3 manage.py migrate_schemas
python3 manage.py collectstatic --noinput

gunicorn --bind 0.0.0.0:8000 horilla.wsgi:application
