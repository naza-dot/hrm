from django.contrib import admin
from .models import (
    Account, Customer, Vendor, Invoice, InvoiceLine,
    Bill, BillLine, Payment, BankAccount, BankStatement,
    BankTransaction, Reconciliation, JournalEntry, JournalEntryLine,
)

admin.site.register(Account)
admin.site.register(Customer)
admin.site.register(Vendor)
admin.site.register(Invoice)
admin.site.register(InvoiceLine)
admin.site.register(Bill)
admin.site.register(BillLine)
admin.site.register(Payment)
admin.site.register(BankAccount)
admin.site.register(BankStatement)
admin.site.register(BankTransaction)
admin.site.register(Reconciliation)
admin.site.register(JournalEntry)
admin.site.register(JournalEntryLine)
