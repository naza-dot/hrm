from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path("", views.finance_dashboard, name="finance-dashboard"),

    # Chart of Accounts
    path("accounts/", views.account_list, name="account-list"),
    path("account/create/", views.account_create, name="account-create"),
    path("account/<int:pk>/update/", views.account_update, name="account-update"),
    path("account/<int:pk>/delete/", views.account_delete, name="account-delete"),

    # Journal Entries
    path("journal-entries/", views.journal_entry_list, name="journal-entry-list"),
    path("journal-entry/create/", views.journal_entry_create, name="journal-entry-create"),

    # Customers
    path("customers/", views.customer_list, name="customer-list"),
    path("customer/create/", views.customer_create, name="customer-create"),
    path("customer/<int:pk>/", views.customer_detail, name="customer-detail"),
    path("customer/<int:pk>/update/", views.customer_update, name="customer-update"),
    path("customer/<int:pk>/delete/", views.customer_delete, name="customer-delete"),

    # Vendors
    path("vendors/", views.vendor_list, name="vendor-list"),
    path("vendor/create/", views.vendor_create, name="vendor-create"),
    path("vendor/<int:pk>/", views.vendor_detail, name="vendor-detail"),
    path("vendor/<int:pk>/update/", views.vendor_update, name="vendor-update"),
    path("vendor/<int:pk>/delete/", views.vendor_delete, name="vendor-delete"),

    # Invoices
    path("invoices/", views.invoice_list, name="invoice-list"),
    path("invoice/create/", views.invoice_create, name="invoice-create"),
    path("invoice/<int:pk>/", views.invoice_detail, name="invoice-detail"),
    path("invoice/<int:pk>/update/", views.invoice_update, name="invoice-update"),
    path("invoice/<int:pk>/delete/", views.invoice_delete, name="invoice-delete"),
    path("invoice/<int:pk>/send/", views.invoice_send, name="invoice-send"),
    path("invoice/<int:pk>/register-payment/", views.invoice_register_payment, name="invoice-register-payment"),

    # Bills
    path("bills/", views.bill_list, name="bill-list"),
    path("bill/create/", views.bill_create, name="bill-create"),
    path("bill/<int:pk>/", views.bill_detail, name="bill-detail"),
    path("bill/<int:pk>/update/", views.bill_update, name="bill-update"),
    path("bill/<int:pk>/delete/", views.bill_delete, name="bill-delete"),
    path("bill/<int:pk>/register-payment/", views.bill_register_payment, name="bill-register-payment"),

    # Payments
    path("payments/", views.payment_list, name="payment-list"),
    path("payment/create/", views.payment_create, name="payment-create"),
    path("payment/<int:pk>/delete/", views.payment_delete, name="payment-delete"),

    # Bank Accounts
    path("bank-accounts/", views.bank_account_list, name="bank-account-list"),
    path("bank-account/create/", views.bank_account_create, name="bank-account-create"),
    path("bank-account/<int:pk>/update/", views.bank_account_update, name="bank-account-update"),
    path("bank-account/<int:pk>/delete/", views.bank_account_delete, name="bank-account-delete"),

    # Bank Statements
    path("bank-statements/", views.bank_statement_list, name="bank-statement-list"),
    path("bank-statement/create/", views.bank_statement_create, name="bank-statement-create"),
    path("bank-statement/<int:pk>/", views.bank_statement_detail, name="bank-statement-detail"),
    path("bank-statement/<int:pk>/delete/", views.bank_statement_delete, name="bank-statement-delete"),

    # Reconciliation
    path("reconciliation/", views.reconciliation_view, name="reconciliation"),
    path("reconciliation/<int:pk>/match/", views.reconciliation_match, name="reconciliation-match"),
]
