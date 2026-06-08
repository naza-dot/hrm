from django.urls import reverse
from django.utils.translation import gettext_lazy as _

MENU = _("Finance")
IMG_SRC = "images/ui/finance.svg"

SUBMENUS = [
    {
        "menu": _("Dashboard"),
        "redirect": reverse("finance-dashboard"),
    },
    {
        "menu": _("Chart of Accounts"),
        "redirect": reverse("account-list"),
    },
    {
        "menu": _("Customers"),
        "redirect": reverse("customer-list"),
    },
    {
        "menu": _("Vendors"),
        "redirect": reverse("vendor-list"),
    },
    {
        "menu": _("Invoices"),
        "redirect": reverse("invoice-list"),
    },
    {
        "menu": _("Bills"),
        "redirect": reverse("bill-list"),
    },
    {
        "menu": _("Payments"),
        "redirect": reverse("payment-list"),
    },
    {
        "menu": _("Bank Accounts"),
        "redirect": reverse("bank-account-list"),
    },
    {
        "menu": _("Bank Statements"),
        "redirect": reverse("bank-statement-list"),
    },
    {
        "menu": _("Reconciliation"),
        "redirect": reverse("reconciliation"),
    },
]
