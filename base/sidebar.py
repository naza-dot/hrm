from django.urls import reverse
from django.utils.translation import gettext_lazy as trans

MENU = trans("HMO")
IMG_SRC = "images/ui/grid.svg"

SUBMENUS = [
    {
        "menu": trans("HMO"),
        "redirect": reverse("hmo-user-view"),
    },
]
