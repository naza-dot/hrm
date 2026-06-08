from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from finance.models import (
    Account, JournalEntryLine, Invoice, Bill, Payment,
    Customer, Vendor, BankAccount,
)


def _get_balance(account, as_of=None):
    qs = JournalEntryLine.objects.filter(account=account)
    if as_of:
        qs = qs.filter(journal_entry__entry_date__lte=as_of)
    dr = qs.aggregate(Sum("debit"))["debit__sum"] or 0
    cr = qs.aggregate(Sum("credit"))["credit__sum"] or 0
    if account.account_type in ("asset", "expense"):
        return account.opening_balance + dr - cr
    return account.opening_balance + cr - dr


@login_required
def dashboard(request):
    now = date.today()
    start_of_month = now.replace(day=1)
    end_of_month = now

    income = sum(
        _get_balance(a, as_of=now)
        for a in Account.objects.filter(account_type="income", is_active=True)
        if _get_balance(a, as_of=now) > 0
    )
    expenses = sum(
        _get_balance(a, as_of=now)
        for a in Account.objects.filter(account_type="expense", is_active=True)
        if _get_balance(a, as_of=now) > 0
    )
    net_income = income - expenses

    total_assets = sum(
        _get_balance(a, as_of=now)
        for a in Account.objects.filter(account_type="asset", is_active=True)
    )
    total_liabilities = sum(
        _get_balance(a, as_of=now)
        for a in Account.objects.filter(account_type="liability", is_active=True)
    )
    total_equity = sum(
        _get_balance(a, as_of=now)
        for a in Account.objects.filter(account_type="equity", is_active=True)
    )

    receivables = Invoice.objects.filter(~Q(status__in=["paid", "cancelled"])).aggregate(
        total=Sum("total"), paid=Sum("amount_paid")
    )
    ar = (receivables["total"] or 0) - (receivables["paid"] or 0)

    payables = Bill.objects.filter(~Q(status__in=["paid", "cancelled"])).aggregate(
        total=Sum("total"), paid=Sum("amount_paid")
    )
    ap = (payables["total"] or 0) - (payables["paid"] or 0)

    cash_balance = 0
    for ba in BankAccount.objects.filter(is_active=True):
        stmt = ba.statements.order_by("-statement_date").first()
        if stmt:
            cash_balance += stmt.closing_balance
        else:
            cash_balance += ba.opening_balance

    income_data = []
    for a in Account.objects.filter(account_type="income", is_active=True):
        bal = _get_balance(a, as_of=now)
        if bal:
            income_data.append({"name": a.name, "balance": bal})

    expense_data = []
    for a in Account.objects.filter(account_type="expense", is_active=True):
        bal = _get_balance(a, as_of=now)
        if bal:
            expense_data.append({"name": a.name, "balance": bal})

    context = {
        "net_income": net_income,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity,
        "ar": ar,
        "ap": ap,
        "cash_balance": cash_balance,
        "income_data": income_data,
        "expense_data": expense_data,
        "income": income,
        "expenses": expenses,
    }
    return render(request, "finreports/dashboard.html", context)


@login_required
def profit_loss(request):
    now = date.today()
    from_date = request.GET.get("from_date", now.replace(month=1, day=1))
    to_date = request.GET.get("to_date", now)

    income_accounts = Account.objects.filter(account_type="income", is_active=True)
    expense_accounts = Account.objects.filter(account_type="expense", is_active=True)

    incomes = []
    total_income = 0
    for a in income_accounts:
        bal = _get_balance(a, as_of=to_date) - _get_balance(a, as_of=from_date)
        if bal:
            incomes.append({"name": a.name, "amount": bal})
            total_income += bal

    expenses_list = []
    total_expense = 0
    for a in expense_accounts:
        bal = _get_balance(a, as_of=to_date) - _get_balance(a, as_of=from_date)
        if bal:
            expenses_list.append({"name": a.name, "amount": bal})
            total_expense += bal

    net = total_income - total_expense

    context = {
        "from_date": from_date,
        "to_date": to_date,
        "incomes": incomes,
        "total_income": total_income,
        "expenses": expenses_list,
        "total_expense": total_expense,
        "net_income": net,
    }
    return render(request, "finreports/profit_loss.html", context)


@login_required
def balance_sheet(request):
    as_of = request.GET.get("as_of", date.today())

    asset_accounts = Account.objects.filter(account_type="asset", is_active=True)
    liability_accounts = Account.objects.filter(account_type="liability", is_active=True)
    equity_accounts = Account.objects.filter(account_type="equity", is_active=True)

    assets = []
    total_assets = 0
    for a in asset_accounts:
        bal = _get_balance(a, as_of=as_of)
        if bal:
            assets.append({"name": a.name, "balance": bal})
            total_assets += bal

    liabilities = []
    total_liabilities = 0
    for a in liability_accounts:
        bal = _get_balance(a, as_of=as_of)
        if bal:
            liabilities.append({"name": a.name, "balance": bal})
            total_liabilities += bal

    equities = []
    total_equity = 0
    for a in equity_accounts:
        bal = _get_balance(a, as_of=as_of)
        if bal:
            equities.append({"name": a.name, "balance": bal})
            total_equity += bal

    context = {
        "as_of": as_of,
        "assets": assets,
        "total_assets": total_assets,
        "liabilities": liabilities,
        "total_liabilities": total_liabilities,
        "equities": equities,
        "total_equity": total_equity,
        "total_liabilities_equity": total_liabilities + total_equity,
    }
    return render(request, "finreports/balance_sheet.html", context)


@login_required
def cash_flow(request):
    now = date.today()
    from_date = request.GET.get("from_date", now.replace(month=1, day=1))
    to_date = request.GET.get("to_date", now)

    payments_in = Payment.objects.filter(
        payment_type="incoming",
        payment_date__gte=from_date,
        payment_date__lte=to_date,
    ).aggregate(Sum("amount"))["amount__sum"] or 0

    payments_out = Payment.objects.filter(
        payment_type="outgoing",
        payment_date__gte=from_date,
        payment_date__lte=to_date,
    ).aggregate(Sum("amount"))["amount__sum"] or 0

    invoices_created = Invoice.objects.filter(
        invoice_date__gte=from_date, invoice_date__lte=to_date,
    ).aggregate(Sum("total"))["total__sum"] or 0

    bills_created = Bill.objects.filter(
        bill_date__gte=from_date, bill_date__lte=to_date,
    ).aggregate(Sum("total"))["total__sum"] or 0

    net_cash = payments_in - payments_out

    context = {
        "from_date": from_date,
        "to_date": to_date,
        "payments_in": payments_in,
        "payments_out": payments_out,
        "invoices_created": invoices_created,
        "bills_created": bills_created,
        "net_cash": net_cash,
    }
    return render(request, "finreports/cash_flow.html", context)


@login_required
def general_ledger(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    account_id = request.GET.get("account")

    lines = JournalEntryLine.objects.select_related(
        "journal_entry", "account"
    ).order_by("journal_entry__entry_date")

    if from_date:
        lines = lines.filter(journal_entry__entry_date__gte=from_date)
    if to_date:
        lines = lines.filter(journal_entry__entry_date__lte=to_date)
    if account_id:
        lines = lines.filter(account_id=account_id)

    accounts = Account.objects.filter(is_active=True)

    entries = []
    for line in lines:
        entries.append({
            "date": line.journal_entry.entry_date,
            "entry_number": line.journal_entry.entry_number,
            "account": line.account.name,
            "description": line.description or line.journal_entry.description,
            "debit": line.debit,
            "credit": line.credit,
        })

    context = {
        "entries": entries,
        "accounts": accounts,
        "from_date": from_date or "",
        "to_date": to_date or "",
        "account_id": account_id or "",
    }
    return render(request, "finreports/general_ledger.html", context)


@login_required
def trial_balance(request):
    as_of = request.GET.get("as_of", date.today())
    accounts = Account.objects.filter(is_active=True)

    tb_entries = []
    total_dr = 0
    total_cr = 0
    for a in accounts:
        bal = _get_balance(a, as_of=as_of)
        if bal == 0:
            continue
        dr = bal if a.account_type in ("asset", "expense") else 0
        cr = bal if a.account_type in ("liability", "equity", "income") else 0
        tb_entries.append({
            "code": a.code,
            "name": a.name,
            "debit": dr if dr > 0 else 0,
            "credit": cr if cr > 0 else 0,
        })
        total_dr += dr
        total_cr += cr

    context = {
        "as_of": as_of,
        "entries": tb_entries,
        "total_dr": total_dr,
        "total_cr": total_cr,
    }
    return render(request, "finreports/trial_balance.html", context)


@login_required
def ar_aging(request):
    now = date.today()

    aging_buckets = {
        "0-30": {"label": "0-30 " + str(_("Days")), "total": 0, "items": []},
        "31-60": {"label": "31-60 " + str(_("Days")), "total": 0, "items": []},
        "61-90": {"label": "61-90 " + str(_("Days")), "total": 0, "items": []},
        "90+": {"label": "90+ " + str(_("Days")), "total": 0, "items": []},
    }

    invoices = Invoice.objects.filter(~Q(status__in=["paid", "cancelled"]))

    for inv in invoices:
        due = inv.balance_due()
        if due <= 0:
            continue
        days = (now - inv.due_date).days if inv.due_date < now else 0
        if days <= 30:
            bucket = "0-30"
        elif days <= 60:
            bucket = "31-60"
        elif days <= 90:
            bucket = "61-90"
        else:
            bucket = "90+"

        aging_buckets[bucket]["items"].append({
            "customer": inv.customer.name,
            "invoice": inv.invoice_number,
            "date": inv.invoice_date,
            "due_date": inv.due_date,
            "total": inv.total,
            "due": due,
            "days": days,
        })
        aging_buckets[bucket]["total"] += due

    total_ar = sum(b["total"] for b in aging_buckets.values())

    context = {
        "buckets": aging_buckets,
        "total_ar": total_ar,
        "as_of": now,
    }
    return render(request, "finreports/ar_aging.html", context)


@login_required
def ap_aging(request):
    now = date.today()

    aging_buckets = {
        "0-30": {"label": "0-30 " + str(_("Days")), "total": 0, "items": []},
        "31-60": {"label": "31-60 " + str(_("Days")), "total": 0, "items": []},
        "61-90": {"label": "61-90 " + str(_("Days")), "total": 0, "items": []},
        "90+": {"label": "90+ " + str(_("Days")), "total": 0, "items": []},
    }

    bills = Bill.objects.filter(~Q(status__in=["paid", "cancelled"]))

    for b in bills:
        due = b.balance_due()
        if due <= 0:
            continue
        days = (now - b.due_date).days if b.due_date < now else 0
        if days <= 30:
            bucket = "0-30"
        elif days <= 60:
            bucket = "31-60"
        elif days <= 90:
            bucket = "61-90"
        else:
            bucket = "90+"

        aging_buckets[bucket]["items"].append({
            "vendor": b.vendor.name,
            "bill": b.bill_number,
            "date": b.bill_date,
            "due_date": b.due_date,
            "total": b.total,
            "due": due,
            "days": days,
        })
        aging_buckets[bucket]["total"] += due

    total_ap = sum(b["total"] for b in aging_buckets.values())

    context = {
        "buckets": aging_buckets,
        "total_ap": total_ap,
        "as_of": now,
    }
    return render(request, "finreports/ap_aging.html", context)
