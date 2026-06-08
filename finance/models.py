from django.db import models
from django.utils.translation import gettext_lazy as _
from horilla.models import HorillaModel
from base.models import Company
from base.horilla_company_manager import HorillaCompanyManager


ACCOUNT_TYPES = [
    ("asset", _("Asset")),
    ("liability", _("Liability")),
    ("equity", _("Equity")),
    ("income", _("Income")),
    ("expense", _("Expense")),
]

INVOICE_STATUS = [
    ("draft", _("Draft")),
    ("sent", _("Sent")),
    ("partial", _("Partially Paid")),
    ("paid", _("Paid")),
    ("overdue", _("Overdue")),
    ("cancelled", _("Cancelled")),
]

PAYMENT_METHODS = [
    ("cash", _("Cash")),
    ("bank_transfer", _("Bank Transfer")),
    ("check", _("Cheque")),
    ("credit_card", _("Credit Card")),
    ("online", _("Online Payment")),
]

PAYMENT_DIRECTION = [
    ("incoming", _("Incoming")),
    ("outgoing", _("Outgoing")),
]


class Account(HorillaModel):
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Account Code"))
    name = models.CharField(max_length=200, verbose_name=_("Account Name"))
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, verbose_name=_("Account Type"))
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="children", verbose_name=_("Parent Account"),
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Opening Balance"))
    company_id = models.ManyToManyField(Company, blank=True, verbose_name=_("Company"))
    objects = HorillaCompanyManager()

    class Meta:
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def balance(self):
        from django.db.models import Sum
        from .models import JournalEntryLine
        dr = JournalEntryLine.objects.filter(account=self).aggregate(Sum("debit"))["debit__sum"] or 0
        cr = JournalEntryLine.objects.filter(account=self).aggregate(Sum("credit"))["credit__sum"] or 0
        if self.account_type in ("asset", "expense"):
            return self.opening_balance + dr - cr
        return self.opening_balance + cr - dr


class JournalEntry(HorillaModel):
    entry_number = models.CharField(max_length=50, unique=True, verbose_name=_("Entry Number"))
    entry_date = models.DateField(verbose_name=_("Entry Date"))
    description = models.TextField(verbose_name=_("Description"))
    reference = models.CharField(max_length=200, blank=True, verbose_name=_("Reference"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Locked"))

    class Meta:
        verbose_name = _("Journal Entry")
        verbose_name_plural = _("Journal Entries")
        ordering = ["-entry_date", "-id"]

    def __str__(self):
        return f"{self.entry_number} - {self.entry_date}"

    def total_debit(self):
        return self.lines.aggregate(models.Sum("debit"))["debit__sum"] or 0

    def total_credit(self):
        return self.lines.aggregate(models.Sum("credit"))["credit__sum"] or 0

    def is_balanced(self):
        return self.total_debit() == self.total_credit()


class JournalEntryLine(models.Model):
    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.CASCADE, related_name="lines",
        verbose_name=_("Journal Entry"),
    )
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="journal_lines",
        verbose_name=_("Account"),
    )
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Debit"))
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Credit"))
    description = models.CharField(max_length=200, blank=True, verbose_name=_("Description"))

    class Meta:
        verbose_name = _("Journal Entry Line")
        verbose_name_plural = _("Journal Entry Lines")

    def __str__(self):
        return f"{self.journal_entry.entry_number} - {self.account.name}"


class Customer(HorillaModel):
    name = models.CharField(max_length=200, verbose_name=_("Customer Name"))
    contact_person = models.CharField(max_length=200, blank=True, verbose_name=_("Contact Person"))
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    phone = models.CharField(max_length=50, blank=True, verbose_name=_("Phone"))
    address = models.TextField(blank=True, verbose_name=_("Address"))
    tax_id = models.CharField(max_length=100, blank=True, verbose_name=_("Tax ID"))
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Credit Limit"))
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Opening Balance"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    company_id = models.ManyToManyField(Company, blank=True, verbose_name=_("Company"))
    objects = HorillaCompanyManager()

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def total_invoiced(self):
        return self.invoices.aggregate(models.Sum("total"))["total__sum"] or 0

    def total_paid(self):
        return self.invoices.aggregate(models.Sum("amount_paid"))["amount_paid__sum"] or 0

    def balance_due(self):
        return self.total_invoiced() - self.total_paid()


class Vendor(HorillaModel):
    name = models.CharField(max_length=200, verbose_name=_("Vendor Name"))
    contact_person = models.CharField(max_length=200, blank=True, verbose_name=_("Contact Person"))
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    phone = models.CharField(max_length=50, blank=True, verbose_name=_("Phone"))
    address = models.TextField(blank=True, verbose_name=_("Address"))
    tax_id = models.CharField(max_length=100, blank=True, verbose_name=_("Tax ID"))
    payment_terms = models.CharField(max_length=100, blank=True, verbose_name=_("Payment Terms"))
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Opening Balance"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    company_id = models.ManyToManyField(Company, blank=True, verbose_name=_("Company"))
    objects = HorillaCompanyManager()

    class Meta:
        verbose_name = _("Vendor")
        verbose_name_plural = _("Vendors")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def total_billed(self):
        return self.bills.aggregate(models.Sum("total"))["total__sum"] or 0

    def total_paid(self):
        return self.bills.aggregate(models.Sum("amount_paid"))["amount_paid__sum"] or 0

    def balance_due(self):
        return self.total_billed() - self.total_paid()


class Invoice(HorillaModel):
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name=_("Invoice Number"))
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="invoices",
        verbose_name=_("Customer"),
    )
    invoice_date = models.DateField(verbose_name=_("Invoice Date"))
    due_date = models.DateField(verbose_name=_("Due Date"))
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default="draft", verbose_name=_("Status"))
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Subtotal"))
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Tax Amount"))
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Total"))
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Amount Paid"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="invoices", verbose_name=_("Journal Entry"),
    )
    company_id = models.ManyToManyField(Company, blank=True, verbose_name=_("Company"))
    objects = HorillaCompanyManager("customer__company_id")

    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        ordering = ["-invoice_date", "-id"]

    def __str__(self):
        return self.invoice_number

    def balance_due(self):
        return self.total - self.amount_paid

    def is_overdue(self):
        from django.utils.timezone import now
        from datetime import date
        if self.status not in ("paid", "cancelled") and self.due_date < date.today():
            return True
        return False


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="lines",
        verbose_name=_("Invoice"),
    )
    description = models.CharField(max_length=500, verbose_name=_("Description"))
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name=_("Quantity"))
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_("Unit Price"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_("Tax Rate (%)"))
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_("Amount"))

    class Meta:
        verbose_name = _("Invoice Line")
        verbose_name_plural = _("Invoice Lines")

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description[:50]}"


class Bill(HorillaModel):
    bill_number = models.CharField(max_length=50, unique=True, verbose_name=_("Bill Number"))
    vendor = models.ForeignKey(
        Vendor, on_delete=models.PROTECT, related_name="bills",
        verbose_name=_("Vendor"),
    )
    bill_date = models.DateField(verbose_name=_("Bill Date"))
    due_date = models.DateField(verbose_name=_("Due Date"))
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default="draft", verbose_name=_("Status"))
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Subtotal"))
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Tax Amount"))
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Total"))
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Amount Paid"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="bills", verbose_name=_("Journal Entry"),
    )
    company_id = models.ManyToManyField(Company, blank=True, verbose_name=_("Company"))
    objects = HorillaCompanyManager("vendor__company_id")

    class Meta:
        verbose_name = _("Bill")
        verbose_name_plural = _("Bills")
        ordering = ["-bill_date", "-id"]

    def __str__(self):
        return self.bill_number

    def balance_due(self):
        return self.total - self.amount_paid


class BillLine(models.Model):
    bill = models.ForeignKey(
        Bill, on_delete=models.CASCADE, related_name="lines",
        verbose_name=_("Bill"),
    )
    description = models.CharField(max_length=500, verbose_name=_("Description"))
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name=_("Quantity"))
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_("Unit Price"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_("Tax Rate (%)"))
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_("Amount"))

    class Meta:
        verbose_name = _("Bill Line")
        verbose_name_plural = _("Bill Lines")

    def __str__(self):
        return f"{self.bill.bill_number} - {self.description[:50]}"


class Payment(HorillaModel):
    payment_type = models.CharField(max_length=20, choices=PAYMENT_DIRECTION, verbose_name=_("Payment Type"))
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="payments", verbose_name=_("Customer"),
    )
    vendor = models.ForeignKey(
        Vendor, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="payments", verbose_name=_("Vendor"),
    )
    invoice = models.ForeignKey(
        Invoice, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="payments", verbose_name=_("Invoice"),
    )
    bill = models.ForeignKey(
        Bill, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="payments", verbose_name=_("Bill"),
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_("Amount"))
    payment_date = models.DateField(verbose_name=_("Payment Date"))
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default="bank_transfer", verbose_name=_("Payment Method"))
    reference_number = models.CharField(max_length=100, blank=True, verbose_name=_("Reference Number"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="payments", verbose_name=_("Journal Entry"),
    )
    company_id = models.ManyToManyField(Company, blank=True, verbose_name=_("Company"))
    objects = HorillaCompanyManager()

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ["-payment_date", "-id"]

    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.reference_number or self.id}"


class BankAccount(HorillaModel):
    account_name = models.CharField(max_length=200, verbose_name=_("Account Name"))
    account_number = models.CharField(max_length=50, verbose_name=_("Account Number"))
    bank_name = models.CharField(max_length=200, verbose_name=_("Bank Name"))
    branch = models.CharField(max_length=200, blank=True, verbose_name=_("Branch"))
    ifsc_code = models.CharField(max_length=50, blank=True, verbose_name=_("IFSC/Swift Code"))
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Opening Balance"))
    gl_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="bank_accounts",
        verbose_name=_("GL Account"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    company_id = models.ManyToManyField(Company, blank=True, verbose_name=_("Company"))
    objects = HorillaCompanyManager()

    class Meta:
        verbose_name = _("Bank Account")
        verbose_name_plural = _("Bank Accounts")

    def __str__(self):
        return f"{self.bank_name} - {self.account_name} ({self.account_number})"


class BankStatement(HorillaModel):
    bank_account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name="statements",
        verbose_name=_("Bank Account"),
    )
    statement_date = models.DateField(verbose_name=_("Statement Date"))
    closing_balance = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_("Closing Balance"))
    import_file = models.FileField(upload_to="bank_statements/", null=True, blank=True, verbose_name=_("Import File"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        verbose_name = _("Bank Statement")
        verbose_name_plural = _("Bank Statements")
        ordering = ["-statement_date"]

    def __str__(self):
        return f"{self.bank_account} - {self.statement_date}"

    def total_debits(self):
        return self.transactions.aggregate(models.Sum("debit"))["debit__sum"] or 0

    def total_credits(self):
        return self.transactions.aggregate(models.Sum("credit"))["credit__sum"] or 0

    def reconciled_count(self):
        return self.transactions.filter(reconciled=True).count()

    def unreconciled_count(self):
        return self.transactions.filter(reconciled=False).count()


class BankTransaction(models.Model):
    bank_statement = models.ForeignKey(
        BankStatement, on_delete=models.CASCADE, related_name="transactions",
        verbose_name=_("Bank Statement"),
    )
    date = models.DateField(verbose_name=_("Transaction Date"))
    description = models.CharField(max_length=500, verbose_name=_("Description"))
    reference = models.CharField(max_length=200, blank=True, verbose_name=_("Reference"))
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Debit"))
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Credit"))
    reconciled = models.BooleanField(default=False, verbose_name=_("Reconciled"))

    class Meta:
        verbose_name = _("Bank Transaction")
        verbose_name_plural = _("Bank Transactions")
        ordering = ["date"]

    def __str__(self):
        return f"{self.date} - {self.description[:50]}"


class Reconciliation(models.Model):
    bank_transaction = models.ForeignKey(
        BankTransaction, on_delete=models.CASCADE, related_name="reconciliation_records",
        verbose_name=_("Bank Transaction"),
    )
    reconciled_with_type = models.CharField(max_length=50, verbose_name=_("Reconciled With Type"))
    reconciled_with_id = models.PositiveIntegerField(verbose_name=_("Reconciled With ID"))
    reconciled_date = models.DateField(auto_now_add=True, verbose_name=_("Reconciled Date"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        verbose_name = _("Reconciliation")
        verbose_name_plural = _("Reconciliations")

    def __str__(self):
        return f"Reconciliation {self.id}"
