from django.urls import reverse
from django.utils.translation import gettext_lazy as _

MENU = _("Financial Reports")
IMG_SRC = "images/ui/report.svg"

SUBMENUS = [
    {
        "menu": _("Dashboard"),
        "redirect": reverse("finreports-dashboard"),
    },
    {
        "menu": _("Profit & Loss"),
        "redirect": reverse("profit-loss"),
    },
    {
        "menu": _("Balance Sheet"),
        "redirect": reverse("balance-sheet"),
    },
    {
        "menu": _("Cash Flow Statement"),
        "redirect": reverse("cash-flow"),
    },
    {
        "menu": _("General Ledger"),
        "redirect": reverse("general-ledger"),
    },
    {
        "menu": _("Trial Balance"),
        "redirect": reverse("trial-balance"),
    },
    {
        "menu": _("AR Aging"),
        "redirect": reverse("ar-aging"),
    },
    {
        "menu": _("AP Aging"),
        "redirect": reverse("ap-aging"),
    },
]
