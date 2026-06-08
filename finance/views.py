import json
from datetime import date, datetime
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from base.methods import get_pagination
from .models import (
    Account, Customer, Vendor, Invoice, InvoiceLine,
    Bill, BillLine, Payment, BankAccount, BankStatement,
    BankTransaction, Reconciliation, JournalEntry, JournalEntryLine,
    INVOICE_STATUS,
)
from .forms import (
    AccountForm, CustomerForm, VendorForm, InvoiceForm,
    BillForm, PaymentForm, BankAccountForm, BankStatementForm,
    JournalEntryForm,
)
from .filters import (
    AccountFilter, CustomerFilter, VendorFilter, InvoiceFilter,
    BillFilter, PaymentFilter, BankAccountFilter, BankStatementFilter,
    BankTransactionFilter,
)


# -----------------------------------------------------------
# Helper
# -----------------------------------------------------------
def _paginate(request, queryset, per_page=25):
    paginator = Paginator(queryset, per_page)
    page = request.GET.get("page", 1)
    return paginator.get_page(page)


# -----------------------------------------------------------
# Dashboard
# -----------------------------------------------------------
@login_required
def finance_dashboard(request):
    total_invoices = Invoice.objects.count()
    total_bills = Bill.objects.count()
    total_customers = Customer.objects.filter(is_active=True).count()
    total_vendors = Vendor.objects.filter(is_active=True).count()

    receivables = Invoice.objects.aggregate(
        total=Sum("total"), paid=Sum("amount_paid")
    )
    total_receivables = (receivables["total"] or 0) - (receivables["paid"] or 0)

    payables = Bill.objects.aggregate(
        total=Sum("total"), paid=Sum("amount_paid")
    )
    total_payables = (payables["total"] or 0) - (payables["paid"] or 0)

    unpaid_invoices = Invoice.objects.filter(~Q(status="paid") & ~Q(status="cancelled")).order_by("-invoice_date")[:5]
    unpaid_bills = Bill.objects.filter(~Q(status="paid") & ~Q(status="cancelled")).order_by("-bill_date")[:5]
    recent_payments = Payment.objects.all().order_by("-payment_date")[:5]

    invoices_overdue = Invoice.objects.filter(
        ~Q(status="paid") & ~Q(status="cancelled"),
        due_date__lt=date.today(),
    ).count()

    bills_overdue = Bill.objects.filter(
        ~Q(status="paid") & ~Q(status="cancelled"),
        due_date__lt=date.today(),
    ).count()

    bank_balances = []
    for ba in BankAccount.objects.filter(is_active=True):
        stmts = BankStatement.objects.filter(bank_account=ba).order_by("-statement_date")
        if stmts.exists():
            bank_balances.append({"account": ba, "balance": stmts.first().closing_balance})
        else:
            bank_balances.append({"account": ba, "balance": ba.opening_balance})

    context = {
        "total_invoices": total_invoices,
        "total_bills": total_bills,
        "total_customers": total_customers,
        "total_vendors": total_vendors,
        "total_receivables": total_receivables,
        "total_payables": total_payables,
        "unpaid_invoices": unpaid_invoices,
        "unpaid_bills": unpaid_bills,
        "recent_payments": recent_payments,
        "invoices_overdue": invoices_overdue,
        "bills_overdue": bills_overdue,
        "bank_balances": bank_balances,
    }
    return render(request, "finance/dashboard.html", context)


# -----------------------------------------------------------
# Chart of Accounts
# -----------------------------------------------------------
@login_required
def account_list(request):
    f = AccountFilter(request.GET, queryset=Account.objects.all())
    accounts = _paginate(request, f.qs)
    context = {
        "accounts": accounts,
        "filters": f,
        "filter_dict": request.GET,
    }
    return render(request, "finance/account_list.html", context)


@login_required
def account_create(request):
    form = AccountForm()
    if request.method == "POST":
        form = AccountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Account created successfully."))
            return redirect("account-list")
    return render(request, "finance/form.html", {
        "form": form, "title": _("Create Account"),
        "action": "account-create",
    })


@login_required
def account_update(request, pk):
    account = get_object_or_404(Account, pk=pk)
    form = AccountForm(instance=account)
    if request.method == "POST":
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, _("Account updated successfully."))
            return redirect("account-list")
    return render(request, "finance/form.html", {
        "form": form, "title": _("Update Account"),
        "action": "account-update", "pk": pk,
    })


@login_required
def account_delete(request, pk):
    account = get_object_or_404(Account, pk=pk)
    if request.method == "POST":
        account.delete()
        messages.success(request, _("Account deleted."))
        return redirect("account-list")
    return render(request, "finance/confirm_delete.html", {
        "object": account, "action": "account-delete",
    })


# -----------------------------------------------------------
# Journal Entries
# -----------------------------------------------------------
@login_required
def journal_entry_list(request):
    entries = JournalEntry.objects.all().order_by("-entry_date", "-id")
    entries = _paginate(request, entries)
    context = {"entries": entries}
    return render(request, "finance/journal_entry_list.html", context)


@login_required
def journal_entry_create(request):
    form = JournalEntryForm()
    if request.method == "POST":
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            je = form.save()
            messages.success(request, _("Journal entry created. Add lines to balance it."))
            return redirect("journal-entry-list")
    return render(request, "finance/form.html", {
        "form": form, "title": _("Create Journal Entry"),
        "action": "journal-entry-create",
    })


# -----------------------------------------------------------
# Customers
# -----------------------------------------------------------
@login_required
def customer_list(request):
    f = CustomerFilter(request.GET, queryset=Customer.objects.all())
    customers = _paginate(request, f.qs)
    context = {"customers": customers, "filters": f, "filter_dict": request.GET}
    return render(request, "finance/customer_list.html", context)


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    invoices = customer.invoices.all().order_by("-invoice_date")
    payments = customer.payments.all().order_by("-payment_date")
    context = {
        "customer": customer,
        "invoices": invoices,
        "payments": payments,
    }
    return render(request, "finance/customer_detail.html", context)


@login_required
def customer_create(request):
    form = CustomerForm()
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Customer created successfully."))
            return redirect("customer-list")
    return render(request, "finance/form.html", {
        "form": form, "title": _("Create Customer"),
        "action": "customer-create",
    })


@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(instance=customer)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, _("Customer updated successfully."))
            return redirect("customer-list")
    return render(request, "finance/form.html", {
        "form": form, "title": _("Update Customer"),
        "action": "customer-update", "pk": pk,
    })


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        customer.delete()
        messages.success(request, _("Customer deleted."))
        return redirect("customer-list")
    return render(request, "finance/confirm_delete.html", {
        "object": customer, "action": "customer-delete",
    })


# -----------------------------------------------------------
# Vendors
# -----------------------------------------------------------
@login_required
def vendor_list(request):
    f = VendorFilter(request.GET, queryset=Vendor.objects.all())
    vendors = _paginate(request, f.qs)
    context = {"vendors": vendors, "filters": f, "filter_dict": request.GET}
    return render(request, "finance/vendor_list.html", context)


@login_required
def vendor_detail(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    bills = vendor.bills.all().order_by("-bill_date")
    payments = vendor.payments.all().order_by("-payment_date")
    context = {"vendor": vendor, "bills": bills, "payments": payments}
    return render(request, "finance/vendor_detail.html", context)


@login_required
def vendor_create(request):
    form = VendorForm()
    if request.method == "POST":
        form = VendorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Vendor created successfully."))
            return redirect("vendor-list")
    return render(request, "finance/form.html", {
        "form": form, "title": _("Create Vendor"),
        "action": "vendor-create",
    })


@login_required
def vendor_update(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    form = VendorForm(instance=vendor)
    if request.method == "POST":
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, _("Vendor updated successfully."))
            return redirect("vendor-list")
    return render(request, "finance/form.html", {
        "form": form, "title": _("Update Vendor"),
        "action": "vendor-update", "pk": pk,
    })


@login_required
def vendor_delete(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == "POST":
        vendor.delete()
        messages.success(request, _("Vendor deleted."))
        return redirect("vendor-list")
    return render(request, "finance/confirm_delete.html", {
        "object": vendor, "action": "vendor-delete",
    })


# -----------------------------------------------------------
# Invoices
# -----------------------------------------------------------
@login_required
def invoice_list(request):
    f = InvoiceFilter(request.GET, queryset=Invoice.objects.all())
    invoices = _paginate(request, f.qs)
    context = {"invoices": invoices, "filters": f, "filter_dict": request.GET}
    return render(request, "finance/invoice_list.html", context)


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    context = {"invoice": invoice}
    return render(request, "finance/invoice_detail.html", context)


@login_required
def invoice_create(request):
    form = InvoiceForm()
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save()
            lines_data = json.loads(request.POST.get("lines", "[]"))
            for line_data in lines_data:
                InvoiceLine.objects.create(
                    invoice=invoice,
                    description=line_data.get("description", ""),
                    quantity=line_data.get("quantity", 1),
                    unit_price=line_data.get("unit_price", 0),
                    tax_rate=line_data.get("tax_rate", 0),
                    amount=line_data.get("amount", 0),
                )
            messages.success(request, _("Invoice created successfully."))
            return redirect("invoice-list")
        messages.error(request, _("Please correct the errors below."))
    return render(request, "finance/invoice_form.html", {
        "form": form, "title": _("Create Invoice"),
        "action": "invoice-create",
    })


@login_required
def invoice_update(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    form = InvoiceForm(instance=invoice)
    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            invoice = form.save()
            invoice.lines.all().delete()
            lines_data = json.loads(request.POST.get("lines", "[]"))
            for line_data in lines_data:
                InvoiceLine.objects.create(
                    invoice=invoice,
                    description=line_data.get("description", ""),
                    quantity=line_data.get("quantity", 1),
                    unit_price=line_data.get("unit_price", 0),
                    tax_rate=line_data.get("tax_rate", 0),
                    amount=line_data.get("amount", 0),
                )
            messages.success(request, _("Invoice updated successfully."))
            return redirect("invoice-list")
    lines = [
        {
            "description": l.description,
            "quantity": str(l.quantity),
            "unit_price": str(l.unit_price),
            "tax_rate": str(l.tax_rate),
            "amount": str(l.amount),
        }
        for l in invoice.lines.all()
    ]
    return render(request, "finance/invoice_form.html", {
        "form": form, "title": _("Update Invoice"),
        "action": "invoice-update", "pk": pk, "existing_lines": json.dumps(lines),
    })


@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == "POST":
        invoice.delete()
        messages.success(request, _("Invoice deleted."))
        return redirect("invoice-list")
    return render(request, "finance/confirm_delete.html", {
        "object": invoice, "action": "invoice-delete",
    })


@login_required
def invoice_send(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.status == "draft":
        invoice.status = "sent"
        invoice.save()
        messages.success(request, _("Invoice marked as sent."))
    return redirect("invoice-list")


@login_required
def invoice_register_payment(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == "POST":
        amount = float(request.POST.get("amount", 0))
        if amount <= 0:
            messages.error(request, _("Amount must be positive."))
            return redirect("invoice-detail", pk=pk)
        Payment.objects.create(
            payment_type="incoming",
            customer=invoice.customer,
            invoice=invoice,
            amount=amount,
            payment_date=request.POST.get("payment_date", date.today()),
            method=request.POST.get("method", "bank_transfer"),
            reference_number=request.POST.get("reference_number", ""),
        )
        invoice.amount_paid = (invoice.amount_paid or 0) + amount
        if invoice.amount_paid >= invoice.total:
            invoice.status = "paid"
        else:
            invoice.status = "partial"
        invoice.save()
        messages.success(request, _("Payment registered for invoice."))
        return redirect("invoice-detail", pk=pk)
    return render(request, "finance/register_payment.html", {
        "invoice": invoice, "type": "invoice",
    })


# -----------------------------------------------------------
# Bills
# -----------------------------------------------------------
@login_required
def bill_list(request):
    f = BillFilter(request.GET, queryset=Bill.objects.all())
    bills = _paginate(request, f.qs)
    context = {"bills": bills, "filters": f, "filter_dict": request.GET}
    return render(request, "finance/bill_list.html", context)


@login_required
def bill_detail(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    context = {"bill": bill}
    return render(request, "finance/bill_detail.html", context)


@login_required
def bill_create(request):
    form = BillForm()
    if request.method == "POST":
        form = BillForm(request.POST)
        if form.is_valid():
            bill = form.save()
            lines_data = json.loads(request.POST.get("lines", "[]"))
            for line_data in lines_data:
                BillLine.objects.create(
                    bill=bill,
                    description=line_data.get("description", ""),
                    quantity=line_data.get("quantity", 1),
                    unit_price=line_data.get("unit_price", 0),
                    tax_rate=line_data.get("tax_rate", 0),
                    amount=line_data.get("amount", 0),
                )
            messages.success(request, _("Bill created successfully."))
            return redirect("bill-list")
    return render(request, "finance/bill_form.html", {
        "form": form, "title": _("Create Bill"),
        "action": "bill-create",
    })


@login_required
def bill_update(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    form = BillForm(instance=bill)
    if request.method == "POST":
        form = BillForm(request.POST, instance=bill)
        if form.is_valid():
            bill = form.save()
            bill.lines.all().delete()
            lines_data = json.loads(request.POST.get("lines", "[]"))
            for line_data in lines_data:
                BillLine.objects.create(
                    bill=bill,
                    description=line_data.get("description", ""),
                    quantity=line_data.get("quantity", 1),
                    unit_price=line_data.get("unit_price", 0),
                    tax_rate=line_data.get("tax_rate", 0),
                    amount=line_data.get("amount", 0),
                )
            messages.success(request, _("Bill updated successfully."))
            return redirect("bill-list")
    lines = [
        {
            "description": l.description,
            "quantity": str(l.quantity),
            "unit_price": str(l.unit_price),
            "tax_rate": str(l.tax_rate),
            "amount": str(l.amount),
        }
        for l in bill.lines.all()
    ]
    return render(request, "finance/bill_form.html", {
        "form": form, "title": _("Update Bill"),
        "action": "bill-update", "pk": pk, "existing_lines": json.dumps(lines),
    })


@login_required
def bill_delete(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == "POST":
        bill.delete()
        messages.success(request, _("Bill deleted."))
        return redirect("bill-list")
    return render(request, "finance/confirm_delete.html", {
        "object": bill, "action": "bill-delete",
    })


@login_required
def bill_register_payment(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == "POST":
        amount = float(request.POST.get("amount", 0))
        if amount <= 0:
            messages.error(request, _("Amount must be positive."))
            return redirect("bill-detail", pk=pk)
        Payment.objects.create(
            payment_type="outgoing",
            vendor=bill.vendor,
            bill=bill,
            amount=amount,
            payment_date=request.POST.get("payment_date", date.today()),
            method=request.POST.get("method", "bank_transfer"),
            reference_number=request.POST.get("reference_number", ""),
        )
        bill.amount_paid = (bill.amount_paid or 0) + amount
        if bill.amount_paid >= bill.total:
            bill.status = "paid"
        else:
            bill.status = "partial"
        bill.save()
        messages.success(request, _("Payment registered for bill."))
        return redirect("bill-detail", pk=pk)
    return render(request, "finance/register_payment.html", {
        "bill": bill, "type": "bill",
    })


# -----------------------------------------------------------
# Payments
# -----------------------------------------------------------
@login_required
def payment_list(request):
    f = PaymentFilter(request.GET, queryset=Payment.objects.all())
    payments = _paginate(request, f.qs)
    context = {"payments": payments, "filters": f, "filter_dict": request.GET}
    return render(request, "finance/payment_list.html", context)


@login_required
def payment_create(request):
    form = PaymentForm()
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            if payment.invoice:
                inv = payment.invoice
                inv.amount_paid = (inv.amount_paid or 0) + payment.amount
                if inv.amount_paid >= inv.total:
                    inv.status = "paid"
                else:
                    inv.status = "partial"
                inv.save()
            if payment.bill:
                bl = payment.bill
                bl.amount_paid = (bl.amount_paid or 0) + payment.amount
                if bl.amount_paid >= bl.total:
                    bl.status = "paid"
                else:
                    bl.status = "partial"
                bl.save()
            messages.success(request, _("Payment recorded successfully."))
            return redirect("payment-list")
    return render(request, "finance/form.html", {
        "form": form, "title": _("Record Payment"),
        "action": "payment-create",
    })


@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == "POST":
        if payment.invoice:
            inv = payment.invoice
            inv.amount_paid = max(0, (inv.amount_paid or 0) - payment.amount)
            if inv.amount_paid <= 0:
                inv.status = "sent"
            else:
                inv.status = "partial"
            inv.save()
        if payment.bill:
            bl = payment.bill
            bl.amount_paid = max(0, (bl.amount_paid or 0) - payment.amount)
            if bl.amount_paid <= 0:
                bl.status = "sent"
            else:
                bl.status = "partial"
            bl.save()
        payment.delete()
        messages.success(request, _("Payment deleted."))
        return redirect("payment-list")
    return render(request, "finance/confirm_delete.html", {
        "object": payment, "action": "payment-delete",
    })


# -----------------------------------------------------------
# Bank Accounts
# -----------------------------------------------------------
@login_required
def bank_account_list(request):
    f = BankAccountFilter(request.GET, queryset=BankAccount.objects.all())
    accounts = _paginate(request, f.qs)
    context = {"bank_accounts": accounts, "filters": f, "filter_dict": request.GET}
    return render(request, "finance/bank_account_list.html", context)


@login_required
def bank_account_create(request):
    form = BankAccountForm()
    if request.method == "POST":
        form = BankAccountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Bank account created successfully."))
            return redirect("bank-account-list")
    return render(request, "finance/form.html", {
        "form": form, "title": _("Create Bank Account"),
        "action": "bank-account-create",
    })


@login_required
def bank_account_update(request, pk):
    ba = get_object_or_404(BankAccount, pk=pk)
    form = BankAccountForm(instance=ba)
    if request.method == "POST":
        form = BankAccountForm(request.POST, instance=ba)
        if form.is_valid():
            form.save()
            messages.success(request, _("Bank account updated."))
            return redirect("bank-account-list")
    return render(request, "finance/form.html", {
        "form": form, "title": _("Update Bank Account"),
        "action": "bank-account-update", "pk": pk,
    })


@login_required
def bank_account_delete(request, pk):
    ba = get_object_or_404(BankAccount, pk=pk)
    if request.method == "POST":
        ba.delete()
        messages.success(request, _("Bank account deleted."))
        return redirect("bank-account-list")
    return render(request, "finance/confirm_delete.html", {
        "object": ba, "action": "bank-account-delete",
    })


# -----------------------------------------------------------
# Bank Statements
# -----------------------------------------------------------
@login_required
def bank_statement_list(request):
    f = BankStatementFilter(request.GET, queryset=BankStatement.objects.all())
    statements = _paginate(request, f.qs)
    context = {"statements": statements, "filters": f, "filter_dict": request.GET}
    return render(request, "finance/bank_statement_list.html", context)


@login_required
def bank_statement_create(request):
    form = BankStatementForm()
    if request.method == "POST":
        form = BankStatementForm(request.POST, request.FILES)
        if form.is_valid():
            statement = form.save()
            if statement.import_file:
                _import_statement_csv(statement)
            messages.success(request, _("Bank statement created."))
            return redirect("bank-statement-list")
    return render(request, "finance/form.html", {
        "form": form, "title": _("Import Bank Statement"),
        "action": "bank-statement-create",
    })


def _import_statement_csv(statement):
    import csv
    import io

    try:
        content = statement.import_file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            debit = float(row.get("debit", 0) or 0)
            credit = float(row.get("credit", 0) or 0)
            BankTransaction.objects.create(
                bank_statement=statement,
                date=row.get("date", date.today()),
                description=row.get("description", ""),
                reference=row.get("reference", ""),
                debit=debit,
                credit=credit,
            )
    except Exception:
        pass


@login_required
def bank_statement_detail(request, pk):
    statement = get_object_or_404(BankStatement, pk=pk)
    f = BankTransactionFilter(request.GET, queryset=statement.transactions.all())
    transactions = _paginate(request, f.qs)
    context = {
        "statement": statement,
        "transactions": transactions,
        "filters": f,
        "filter_dict": request.GET,
    }
    return render(request, "finance/bank_statement_detail.html", context)


@login_required
def bank_statement_delete(request, pk):
    stmt = get_object_or_404(BankStatement, pk=pk)
    if request.method == "POST":
        stmt.delete()
        messages.success(request, _("Bank statement deleted."))
        return redirect("bank-statement-list")
    return render(request, "finance/confirm_delete.html", {
        "object": stmt, "action": "bank-statement-delete",
    })


# -----------------------------------------------------------
# Reconciliation
# -----------------------------------------------------------
@login_required
def reconciliation_view(request):
    bank_account_id = request.GET.get("bank_account")
    bank_accounts = BankAccount.objects.filter(is_active=True)
    transactions = BankTransaction.objects.filter(reconciled=False)

    if bank_account_id:
        transactions = transactions.filter(
            bank_statement__bank_account_id=bank_account_id,
        )

    transactions = _paginate(request, transactions)
    context = {
        "transactions": transactions,
        "bank_accounts": bank_accounts,
        "selected_bank": bank_account_id,
        "invoices": Invoice.objects.filter(~Q(status__in=["paid", "cancelled"])),
        "bills": Bill.objects.filter(~Q(status__in=["paid", "cancelled"])),
    }
    return render(request, "finance/reconciliation.html", context)


@login_required
def reconciliation_match(request, pk):
    transaction = get_object_or_404(BankTransaction, pk=pk)
    if request.method == "POST":
        match_type = request.POST.get("match_type")
        match_id = request.POST.get("match_id")
        if match_type and match_id:
            Reconciliation.objects.create(
                bank_transaction=transaction,
                reconciled_with_type=match_type,
                reconciled_with_id=int(match_id),
            )
            transaction.reconciled = True
            transaction.save()
            messages.success(request, _("Transaction reconciled."))
        else:
            messages.error(request, _("Please select a match."))
        return redirect("reconciliation")
    return render(request, "finance/reconciliation_match.html", {
        "transaction": transaction,
        "invoices": Invoice.objects.filter(~Q(status__in=["paid", "cancelled"])),
        "bills": Bill.objects.filter(~Q(status__in=["paid", "cancelled"])),
    })
