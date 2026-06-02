from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Client, Domain


class DomainInline(admin.TabularInline):
    model = Domain
    max_num = 1


@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ["name", "schema_name", "is_active", "paid_until", "created_at"]
    list_filter = ["is_active", "features"]
    search_fields = ["name", "schema_name", "email"]
    inlines = [DomainInline]

    fieldsets = [
        ("Company Info", {
            "fields": ["name", "schema_name", "email", "phone", "address"]
        }),
        ("Subscription", {
            "fields": ["is_active", "paid_until", "max_employees", "features"],
            "description": "Toggle which features this customer has access to.",
        }),
    ]


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ["domain", "tenant", "is_primary"]
    list_filter = ["is_primary"]
