"""
SaaS Architecture Design for Horilla HRM

Three layers needed:
1. Tenant/Company provisioning (DB autonomy)
2. Feature catalog & subscription management
3. Access enforcement
"""

# === LAYER 1: Database Autonomy ===

# Option: Use django-tenants for PostgreSQL schema-per-tenant
# pip install django-tenants

# INSTALLED_APPS setup:
#   INSTALLED_APPS = [
#       'django_tenants',  # must be first
#       ...
#       'tenants',  # your tenant app
#   ]
#   TENANT_MODEL = "tenants.Client"
#   TENANT_DOMAIN_MODEL = "tenants.Domain"

# The Client/Tenant model stores per-company DB config
"""
from django_tenants.models import TenantMixin, DomainMixin

class Client(TenantMixin):
    name = models.CharField(max_length=100)
    paid_until = models.DateField()
    is_active = models.BooleanField(default=True)
    
    # Feature flags stored as JSON
    features = models.JSONField(default=dict)
    
    auto_create_schema = True

class Domain(DomainMixin):
    pass
"""

# === LAYER 2: Feature Catalog & Subscriptions ===

FEATURE_CATALOG = {
    "recruitment": "Recruitment & Hiring",
    "onboarding": "Employee Onboarding",
    "employee": "Employee Management",
    "attendance": "Attendance Tracking",
    "leave": "Leave Management",
    "payroll": "Payroll Processing",
    "pms": "Performance Management",
    "offboarding": "Offboarding",
    "asset": "Asset Management",
    "helpdesk": "Helpdesk / Ticketing",
    "project": "Project Management",
    "biometric": "Biometric Integration",
    "notifications": "Notifications",
}

# === LAYER 3: Access Enforcement ===

"""
Middleware that checks if the tenant's subscription includes the requested feature.
If not, redirects or returns 403.

class FeatureAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Map URL prefixes to feature module names
        self.feature_url_map = {
            '/recruitment': 'recruitment',
            '/onboarding': 'onboarding',
            '/employee': 'employee',
            '/attendance': 'attendance',
            '/leave': 'leave',
            '/payroll': 'payroll',
            '/pms': 'pms',
            '/offboarding': 'offboarding',
            '/asset': 'asset',
            '/helpdesk': 'helpdesk',
            '/project': 'project',
        }
    
    def __call__(self, request):
        # Get current tenant from request (set by django-tenants middleware)
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return self.get_response(request)
        
        # Check if requested path requires a feature
        for prefix, feature in self.feature_url_map.items():
            if request.path.startswith(prefix):
                features = tenant.features or {}
                if not features.get(feature, False):
                    return HttpResponseForbidden(
                        f"This feature ({feature}) is not in your subscription."
                    )
                break
        
        return self.get_response(request)
"""

# === ADMIN PANEL: Subscription Management ===

"""
A Django admin page (or separate portal) where you:
1. Create a new Client/tenant
2. Toggle feature checkboxes from FEATURE_CATALOG
3. Set paid_until / is_active
4. Provision their schema (auto on save with django-tenants)
"""

# === DEPLOYMENT ARCHITECTURE ===

"""
                         ┌─────────────────┐
                         │  Main Router DB  │
                         │  (tenants, users) │
                         └────────┬─────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                  │
         ┌───────▼───────┐ ┌──────▼──────┐  ┌──────▼──────┐
         │  Tenant A DB  │ │ Tenant B DB │  │ Tenant C DB │
         │  (schema)     │ │ (schema)    │  │ (schema)    │
         └───────────────┘ └─────────────┘  └─────────────┘

- Main router DB stores: tenants, domains, users, subscriptions
- Each tenant has their own schema/DB with their HRM data
- django-tenants auto-creates schemas and routes queries
"""
