import django_filters
from django.utils.translation import gettext_lazy as _
from .models import (
    Account, Customer, Vendor, Invoice, Bill, Payment,
    BankAccount, BankStatement, BankTransaction,
    ACCOUNT_TYPES, INVOICE_STATUS, PAYMENT_DIRECTION, PAYMENT_METHODS,
)


class AccountFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains", label=_("Name"))
    account_type = django_filters.ChoiceFilter(choices=ACCOUNT_TYPES, label=_("Type"))

    class Meta:
        model = Account
        fields = ["name", "account_type", "is_active"]


class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains", label=_("Name"))
    email = django_filters.CharFilter(lookup_expr="icontains", label=_("Email"))

    class Meta:
        model = Customer
        fields = ["name", "email", "is_active"]


class VendorFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains", label=_("Name"))
    email = django_filters.CharFilter(lookup_expr="icontains", label=_("Email"))

    class Meta:
        model = Vendor
        fields = ["name", "email", "is_active"]


class InvoiceFilter(django_filters.FilterSet):
    invoice_number = django_filters.CharFilter(lookup_expr="icontains", label=_("Invoice #"))
    customer = django_filters.ModelChoiceFilter(queryset=Customer.objects.all(), label=_("Customer"))
    status = django_filters.ChoiceFilter(choices=INVOICE_STATUS, label=_("Status"))
    invoice_date = django_filters.DateFromToRangeFilter(label=_("Invoice Date"))

    class Meta:
        model = Invoice
        fields = ["invoice_number", "customer", "status"]


class BillFilter(django_filters.FilterSet):
    bill_number = django_filters.CharFilter(lookup_expr="icontains", label=_("Bill #"))
    vendor = django_filters.ModelChoiceFilter(queryset=Vendor.objects.all(), label=_("Vendor"))
    status = django_filters.ChoiceFilter(choices=INVOICE_STATUS, label=_("Status"))
    bill_date = django_filters.DateFromToRangeFilter(label=_("Bill Date"))

    class Meta:
        model = Bill
        fields = ["bill_number", "vendor", "status"]


class PaymentFilter(django_filters.FilterSet):
    payment_type = django_filters.ChoiceFilter(choices=PAYMENT_DIRECTION, label=_("Type"))
    method = django_filters.ChoiceFilter(choices=PAYMENT_METHODS, label=_("Method"))
    payment_date = django_filters.DateFromToRangeFilter(label=_("Payment Date"))

    class Meta:
        model = Payment
        fields = ["payment_type", "method"]


class BankAccountFilter(django_filters.FilterSet):
    account_name = django_filters.CharFilter(lookup_expr="icontains", label=_("Account Name"))
    bank_name = django_filters.CharFilter(lookup_expr="icontains", label=_("Bank Name"))

    class Meta:
        model = BankAccount
        fields = ["account_name", "bank_name", "is_active"]


class BankStatementFilter(django_filters.FilterSet):
    bank_account = django_filters.ModelChoiceFilter(queryset=BankAccount.objects.all(), label=_("Bank Account"))
    statement_date = django_filters.DateFromToRangeFilter(label=_("Statement Date"))

    class Meta:
        model = BankStatement
        fields = ["bank_account"]


class BankTransactionFilter(django_filters.FilterSet):
    description = django_filters.CharFilter(lookup_expr="icontains", label=_("Description"))
    reconciled = django_filters.BooleanFilter(label=_("Reconciled"))
    date = django_filters.DateFromToRangeFilter(label=_("Date"))

    class Meta:
        model = BankTransaction
        fields = ["description", "reconciled"]
