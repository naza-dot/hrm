from django.db import models

from base.horilla_company_manager import HorillaCompanyManager
from base.models import Company


class LDAPSettings(models.Model):
    ldap_server = models.CharField(max_length=255, default="ldap://127.0.0.1:389")
    bind_dn = models.CharField(max_length=255, default="cn=admin,dc=horilla,dc=com")
    bind_password = models.CharField(max_length=255)
    base_dn = models.CharField(max_length=255, default="ou=users,dc=horilla,dc=com")
    company_id = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)
    objects = HorillaCompanyManager("company_id")

    def __str__(self):
        return f"LDAP Settings ({self.ldap_server})"
