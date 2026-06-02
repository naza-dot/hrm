from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Client(TenantMixin):
    name = models.CharField(max_length=100, verbose_name="Company Name")
    schema_name = models.CharField(max_length=63, unique=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    paid_until = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    FEATURES = {
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
        "notifications": "Notifications & Alerts",
        "report": "Reports & Analytics",
    }

    features = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Subscribed Features",
        help_text="JSON object of feature booleans, e.g. {'recruitment': true, 'payroll': false}",
    )

    max_employees = models.IntegerField(null=True, blank=True)

    auto_create_schema = True
    auto_drop_schema = True

    def __str__(self):
        return f"{self.name} ({self.schema_name})"

    def has_feature(self, feature_slug):
        return self.features.get(feature_slug, False)


class Domain(DomainMixin):
    pass
