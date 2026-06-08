from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="finreports-dashboard"),
    path("profit-loss/", views.profit_loss, name="profit-loss"),
    path("balance-sheet/", views.balance_sheet, name="balance-sheet"),
    path("cash-flow/", views.cash_flow, name="cash-flow"),
    path("general-ledger/", views.general_ledger, name="general-ledger"),
    path("trial-balance/", views.trial_balance, name="trial-balance"),
    path("ar-aging/", views.ar_aging, name="ar-aging"),
    path("ap-aging/", views.ap_aging, name="ap-aging"),
]
