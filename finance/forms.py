from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    Account, Customer, Vendor, Invoice, InvoiceLine,
    Bill, BillLine, Payment, BankAccount, BankStatement,
    BankTransaction, JournalEntry, JournalEntryLine,
)


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["code", "name", "account_type", "parent", "description", "opening_balance"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "name", "contact_person", "email", "phone", "address",
            "tax_id", "credit_limit", "opening_balance", "notes",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            "name", "contact_person", "email", "phone", "address",
            "tax_id", "payment_terms", "opening_balance", "notes",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "invoice_number", "customer", "invoice_date", "due_date",
            "subtotal", "tax_amount", "total", "notes",
        ]
        widgets = {
            "invoice_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class InvoiceLineForm(forms.ModelForm):
    class Meta:
        model = InvoiceLine
        fields = ["description", "quantity", "unit_price", "tax_rate", "amount"]


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = [
            "bill_number", "vendor", "bill_date", "due_date",
            "subtotal", "tax_amount", "total", "notes",
        ]
        widgets = {
            "bill_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class BillLineForm(forms.ModelForm):
    class Meta:
        model = BillLine
        fields = ["description", "quantity", "unit_price", "tax_rate", "amount"]


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            "payment_type", "customer", "vendor", "invoice", "bill",
            "amount", "payment_date", "method", "reference_number", "notes",
        ]
        widgets = {
            "payment_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = [
            "account_name", "account_number", "bank_name", "branch",
            "ifsc_code", "opening_balance", "gl_account",
        ]


class BankStatementForm(forms.ModelForm):
    class Meta:
        model = BankStatement
        fields = ["bank_account", "statement_date", "closing_balance", "import_file", "notes"]
        widgets = {
            "statement_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ["entry_number", "entry_date", "description", "reference"]
        widgets = {
            "entry_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class JournalEntryLineForm(forms.ModelForm):
    class Meta:
        model = JournalEntryLine
        fields = ["account", "debit", "credit", "description"]
