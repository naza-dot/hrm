"""
Generate a step-by-step technical how-to document for the Horilla Payroll module.
Covers every permissible action that a client can perform.
"""

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# ── Styles ──────────────────────────────────────────────────────────────────
style = doc.styles['Normal']
font = style.font
font.name = 'Calibri'
font.size = Pt(10.5)

for level in range(1, 4):
    hs = doc.styles[f'Heading {level}']
    hs.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)

# ── Helper functions ─────────────────────────────────────────────────────────
def add_bullet(text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    if bold_prefix:
        run = p.add_run(bold_prefix)
        run.bold = True
        p.add_run(text)
    else:
        p.add_run(text)
    return p

def add_step(number, text):
    """Add a numbered step."""
    p = doc.add_paragraph()
    run = p.add_run(f"{number}. ")
    run.bold = True
    p.add_run(text)
    return p

def add_note(text):
    p = doc.add_paragraph()
    run = p.add_run("Note: ")
    run.bold = True
    run.font.color.rgb = RGBColor(0xCC, 0x66, 0x00)
    p.add_run(text)
    return p

def add_table(headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        hdr.cells[i].text = h
    for row_data in rows:
        row = table.add_row()
        for i, val in enumerate(row_data):
            row.cells[i].text = str(val)

def add_code(text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = 'Consolas'
    run.font.size = Pt(9)
    return p

# ═══════════════════════════════════════════════════════════════════════════
# TITLE PAGE
# ═══════════════════════════════════════════════════════════════════════════
title = doc.add_heading('Horilla HRMS \u2013 Payroll Module', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run('Technical Step-by-Step How-To Guide\nClient Demo & Practice Manual')
run.font.size = Pt(14)
run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = meta.add_run('\nPrepared for: Client Technical Review\nDate: June 10, 2026\nPurpose: Practice all permissible payroll actions while walking through them with the customer')
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS (manual)
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('Table of Contents', level=1)
toc_items = [
    '1.  Prerequisites &amp; Login',
    '2.  Payroll Settings (Currency Symbol)',
    '3.  Filing Statuses &amp; Tax Brackets',
    '4.  Contracts \u2013 Multiple Remuneration Structures',
    '5.  Allowances \u2013 All Types',
    '6.  Deductions \u2013 All Types',
    '7.  Payslip Generation (Individual &amp; Batch)',
    '8.  Payslip Lifecycle (Draft \u2192 Review \u2192 Confirmed \u2192 Paid)',
    '9.  Viewing, PDF Download &amp; Email Delivery',
    '10. Payroll Dashboard &amp; Reporting',
    '11. Excel Export \u2013 Detailed Payslip Reports',
    '12. Loan &amp; Advanced Salary Management',
    '13. Reimbursements &amp; Encashments',
    '14. Adding One-Time / Ad-Hoc Bonuses &amp; Deductions to Payslips',
    '15. Auto Payslip Generation Scheduling',
    '16. Contract Management &amp; Bulk Operations',
    '17. Microsoft Dynamics Integration Strategy',
]
for item in toc_items:
    doc.add_paragraph(item)

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 1. PREREQUISITES & LOGIN
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('1. Prerequisites &amp; Login', level=1)
doc.add_paragraph(
    'Before performing any payroll actions, ensure the following prerequisites are met:'
)
add_bullet('You have admin-level access (permissions: view_, add_, change_, delete_ for all payroll models).')
add_bullet('Employees are already created in the system (HR > Employees).')
add_bullet('Departments, Job Positions, Job Roles, Shifts, and Work Types are configured in the Base module.')
add_bullet('The Horilla instance is running and you are logged in with an admin/HR account.')

doc.add_heading('Login Step by Step', level=2)
add_step(1, 'Open your browser and navigate to your Horilla instance URL.')
add_step(2, 'Enter your username/email and password. (If Microsoft SSO is configured, click "Sign in with Microsoft".)')
add_step(3, 'After login, you should see the main dashboard. The sidebar menu on the left includes a "Payroll" section with sub-menus: Dashboard, Contract, Allowances, Deductions, Payslips, Loan / Advanced Salary, Encashments & Reimbursements, and Federal Tax.')

doc.add_heading('Navigation Path Summary', level=2)
add_table(
    ['Menu Item', 'URL Pattern', 'Typical Path'],
    [
        ['Payroll Dashboard', '/payroll/view-payroll-dashboard/', 'Payroll > Dashboard'],
        ['Contract', '/payroll/view-contract/', 'Payroll > Contract'],
        ['Allowances', '/payroll/view-allowance/', 'Payroll > Allowances'],
        ['Deductions', '/payroll/view-deduction/', 'Payroll > Deductions'],
        ['Payslips', '/payroll/view-payslip/', 'Payroll > Payslips'],
        ['Loan / Advanced Salary', '/payroll/view-loan/', 'Payroll > Loan / Advanced Salary'],
        ['Encashments & Reimbursements', '/payroll/view-reimbursement/', 'Payroll > Encashments & Reimbursements'],
        ['Federal Tax', '/payroll/filing-status-view/', 'Payroll > Federal Tax'],
    ]
)

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 2. PAYROLL SETTINGS (Currency)
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('2. Payroll Settings (Currency Symbol)', level=1)
doc.add_paragraph(
    'Configure the currency symbol and its display position (prefix/postfix). '
    'This affects all payslips and reports.'
)
add_step(1, 'Navigate to Payroll > Contract (any payroll page).')
add_step(2, 'Click the "Settings" icon/button (usually a gear icon, near the top-right).')
add_step(3, 'In the Payroll Settings form, set:',
)
add_bullet('Currency Symbol: e.g., $, EUR, \u00a3, \u00a5')
add_bullet('Position: "Prefix" (symbol before amount, e.g., $1,000) or "Postfix" (symbol after amount, e.g., 1,000$)')
add_step(4, 'Click "Save". The currency will now appear on all payslips and dashboards.')

add_note('If you have multiple companies, each company can have its own currency setting.')
doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 3. FILING STATUSES & TAX BRACKETS
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('3. Filing Statuses &amp; Tax Brackets', level=1)
doc.add_paragraph(
    'Filing Statuses define how taxable income is calculated (based on Basic Pay, Gross Pay, or Taxable Gross Pay). '
    'Tax Brackets define the progressive tax rates for each Filing Status.'
)

doc.add_heading('3.1 Create a Filing Status', level=2)
add_step(1, 'Go to Payroll > Federal Tax.')
add_step(2, 'Click "Create Filing Status".')
add_step(3, 'Fill in the form:')
add_bullet('Filing Status: e.g., "Single", "Married", "Head of Household"')
add_bullet('Based On: Choose "Basic Pay", "Gross Pay", or "Taxable Gross Pay"')
add_bullet('Description: Optional notes about this filing status')
add_step(4, 'Optionally enable "Python Code" for custom tax calculation logic (advanced).')
add_step(5, 'Click "Save".')

doc.add_heading('3.2 Create Tax Brackets for a Filing Status', level=2)
add_step(1, 'From the Filing Status list view, click the "Tax Brackets" button/icon for the desired filing status.')
add_step(2, 'Click "Create Tax Bracket".')
add_step(3, 'Enter:')
add_bullet('Min Income: The minimum taxable income for this bracket (e.g., 0)')
add_bullet('Max Income: The maximum taxable income (leave blank for infinity / top bracket)')
add_bullet('Tax Rate: Percentage rate as a number (e.g., 10 for 10%)')
add_step(4, 'Click "Save".')
add_step(5, 'Repeat to create additional brackets (e.g., 0-10,000 @ 10%; 10,001-50,000 @ 20%; 50,001+ @ 30%).')

doc.add_heading('3.3 Assign Filing Status to a Contract', level=2)
add_step(1, 'Go to Payroll > Contract.')
add_step(2, 'Open an existing contract or create a new one.')
add_step(3, 'In the "Filing Status" dropdown, select the appropriate filing status.')
add_step(4, 'Save the contract.')

add_note('Tax is calculated based on the employee\'s taxable income using the brackets defined for their assigned Filing Status.')
doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 4. CONTRACTS - MULTIPLE REMUNERATION STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('4. Contracts \u2013 Multiple Remuneration Structures', level=1)
doc.add_paragraph(
    'Each employee must have a Contract that defines their wage type (monthly, daily, hourly), '
    'pay frequency (weekly, monthly, semi-monthly), and basic salary. '
    'You can run five (or more) different remuneration structures simultaneously by creating '
    'different contracts for different employees.'
)

doc.add_heading('4.1 Create a New Contract', level=2)
add_step(1, 'Go to Payroll > Contract.')
add_step(2, 'Click "Create Contract".')
add_step(3, 'Fill in the fields:')
add_table(
    ['Field', 'Description', 'Example Values'],
    [
        ['Contract Title', 'A name for this contract', 'John Smith - Monthly Salary'],
        ['Employee', 'Select the employee', 'John Smith'],
        ['Start Date', 'When this contract begins', '2026-01-01'],
        ['End Date', '(Optional) Contract end date', '2026-12-31'],
        ['Wage Type', 'How the employee is paid', 'Monthly / Daily / Hourly'],
        ['Pay Frequency', 'How often payroll runs', 'Weekly / Monthly / Semi-Monthly'],
        ['Basic Salary', 'The base pay amount', '5000.00'],
        ['Filing Status', 'Tax filing status', 'Single'],
        ['Department', '(Auto-filled from employee info)', 'Engineering'],
        ['Job Position', '(Auto-filled)', 'Senior Developer'],
        ['Shift', '(Auto-filled)', 'General'],
        ['Work Type', '(Auto-filled)', 'Full-Time'],
        ['Status', 'Draft or Active', 'Active'],
        ['Deduct Leave From Basic Pay', 'Auto-calculate leave deductions', 'Checked (default)'],
        ['Calculate Daily Leave Amount', 'Divide basic pay by working days', 'Checked (default)'],
    ]
)
add_step(4, 'Click "Save". The contract is created. Only one "Active" contract can exist per employee at a time.')
add_step(5, 'Repeat for each employee. Different employees can have different wage types, '
             'pay frequencies, and salaries, enabling multiple concurrent remuneration structures.')

doc.add_heading('4.2 Example: Five Remuneration Structures', level=2)
add_table(
    ['Structure', 'Wage Type', 'Pay Frequency', 'Example Group'],
    [
        ['Monthly Salaried', 'Monthly', 'Monthly', 'Management Team'],
        ['Hourly Workers', 'Hourly', 'Weekly', 'Part-Time Staff'],
        ['Commission-Based', 'Monthly (Commission)', 'Monthly', 'Sales Team'],
        ['Daily Wage Workers', 'Daily', 'Weekly', 'Contract Labour'],
        ['Executive / Contractors', 'Monthly', 'Semi-Monthly', 'Senior Consultants'],
    ]
)

doc.add_heading('4.3 Managing Contracts', level=2)
add_bullet('View all contracts: Payroll > Contract')
add_bullet('Filter contracts: Use the filter form by employee, department, status, date range.')
add_bullet('Update contract status: Click the status badge or use the bulk actions menu. Statuses: Draft, Active, Expired, Terminated.', bold_prefix='Bulk Status Update: ')
add_bullet('Export contracts: From the Contract view, click "Export" to download contract data as Excel.')
add_bullet('Delete contracts: Check the box(es) and use the bulk delete action, or delete individually.')

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 5. ALLOWANCES
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('5. Allowances \u2013 All Types', level=1)
doc.add_paragraph(
    'Allowances are extra payments added to the basic salary. '
    'Horilla supports a wide variety of allowance types. Each allowance is a reusable building block '
    'that is automatically applied to qualifying payslips.'
)

doc.add_heading('5.1 Supported Allowance Types', level=2)
add_bullet('Fixed amount (e.g., $200 travel allowance per month)')
add_bullet('Percentage of Basic Pay (e.g., 10% housing allowance)')
add_bullet('Based on Attendance (e.g., $10 per validated attendance day)')
add_bullet('Based on Shift (e.g., $15 extra per night shift)')
add_bullet('Based on Work Type (e.g., extra pay for hazardous duty)')
add_bullet('Overtime-Based (e.g., $25 per hour of approved overtime)')
add_bullet('Based on Number of Children (e.g., child education allowance)')
add_bullet('Condition-Based (e.g., only applies to employees in a specific department)')
add_bullet('One-Time or Recurring')
add_bullet('Taxable or Non-Taxable')
add_bullet('With maximum limits / caps')

doc.add_heading('5.2 Create a Fixed Allowance', level=2)
add_step(1, 'Go to Payroll > Allowances.')
add_step(2, 'Click "Create Allowance".')
add_step(3, 'Enter the Title (e.g., "Travel Allowance").')
add_step(4, 'Check "Is Fixed" (the default).')
add_step(5, 'Enter the Amount (e.g., 200).')
add_step(6, 'Set Targeting:')
add_bullet('"Include all active employees": Check to apply to everyone.')
add_bullet('"Employees Specific": Select individual employees.')
add_bullet('"Exclude Employees": Exclude specific employees.')
add_step(7, 'Set "Is Taxable": Check if this allowance should be included in taxable income.')
add_step(8, 'Optional: Set "Has Max Limit" and enter a maximum amount.')
add_step(9, 'Optional: Set "If Condition" to only apply the allowance when certain pay-head conditions are met '
             '(e.g., only apply if Basic Pay > $2,000).')
add_step(10, 'Click "Save".')

doc.add_heading('5.3 Create a Percentage-Based Allowance', level=2)
add_step(1, 'Go to Payroll > Allowances > Create Allowance.')
add_step(2, 'Enter Title (e.g., "Housing Allowance").')
add_step(3, 'Uncheck "Is Fixed" (this enables formula-based calculation).')
add_step(4, 'Select "Based On": Choose "Basic Pay", "Children", "Attendance", "Shift", "Work Type", or "Overtime".')
add_step(5, 'If based on Basic Pay: Enter the Rate as a percentage (e.g., 10 for 10%).')
add_step(6, 'If based on Attendance: Enter the "Per Attendance Fixed Amount" (e.g., 10 per day).')
add_step(7, 'If based on Shift: Select the Shift and enter the "Shift Per Attendance Amount".')
add_step(8, 'If based on Overtime: Enter the "Amount Per One Hour".')
add_step(9, 'If based on Children: Enter the "Per Children Fixed Amount".')
add_step(10, 'Configure targeting, taxability, conditions, and click "Save".')

doc.add_heading('5.4 Create a Condition-Based Allowance', level=2)
add_step(1, 'Follow steps 1-5 above for any allowance type.')
add_step(2, 'Check "Is Condition Based".')
add_step(3, 'Set the Field (e.g., "Department on Contract"), Condition (e.g., "Equal"), '
             'and Value (e.g., "Sales").')
add_step(4, 'Only employees matching the condition will receive this allowance.')
add_step(5, 'Click "Save".')

doc.add_heading('5.5 Managing Allowances', level=2)
add_bullet('View: Payroll > Allowances')
add_bullet('Edit: Click the allowance title or the edit icon.')
add_bullet('Delete: Use the delete icon or bulk action.')
add_bullet('Filter: Use the filter form by title, amount, condition, etc.')

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 6. DEDUCTIONS
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('6. Deductions \u2013 All Types', level=1)
doc.add_paragraph(
    'Deductions are amounts subtracted from an employee\'s pay. They can be pre-tax, post-tax, or tax deductions. '
    'Like allowances, deductions are reusable building blocks.'
)

doc.add_heading('6.1 Supported Deduction Types', level=2)
add_bullet('Fixed amount (e.g., $50 union fee)')
add_bullet('Percentage of Basic Pay, Gross Pay, Taxable Gross Pay, or Net Pay')
add_bullet('Pre-tax deductions (reduce taxable income)')
add_bullet('Post-tax deductions (deducted after tax calculation)')
add_bullet('Tax deductions (income tax withholding)')
add_bullet('Employer contributions (company\'s share, tracked separately)')
add_bullet('Condition-based (e.g., only for specific locations)')
add_bullet('Loan instalments (auto-generated when creating loans)')
add_bullet('With maximum limits and threshold conditions')

doc.add_heading('6.2 Create a Fixed Deduction', level=2)
add_step(1, 'Go to Payroll > Deductions.')
add_step(2, 'Click "Create Deduction".')
add_step(3, 'Enter Title (e.g., "Union Dues").')
add_step(4, 'Check "Is Fixed".')
add_step(5, 'Enter the Amount (e.g., 50).')
add_step(6, 'Set the deduction type:')
add_bullet('"Is Pretax": Check to reduce taxable income (e.g., 401k contributions).')
add_bullet('"Is Tax": Check if this is a tax deduction (e.g., income tax).')
add_step(7, 'Configure targeting (all employees, specific, exclude).')
add_step(8, 'Optional: Configure "Update Compensation" to adjust a pay-head before other deductions start.')
add_step(9, 'Optional: Employer Rate to track employer-side contributions separately.')
add_step(10, 'Optional: Max limit and If conditions.')
add_step(11, 'Click "Save".')

doc.add_heading('6.3 Create a Percentage-Based Deduction', level=2)
add_step(1, 'Go to Payroll > Deductions > Create Deduction.')
add_step(2, 'Enter Title (e.g., "Pension Contribution").')
add_step(3, 'Uncheck "Is Fixed".')
add_step(4, 'Select "Based On": Basic Pay, Gross Pay, Taxable Gross Pay, or Net Pay.')
add_step(5, 'Enter the Employee Rate (e.g., 5 for 5%).')
add_step(6, 'Optionally enter the Employer Rate (e.g., 5 for 5% employer match).')
add_step(7, 'Configure pre-tax/post-tax, targeting, conditions, and click "Save".')

doc.add_heading('6.4 Managing Deductions', level=2)
add_bullet('View, edit, delete, and filter deductions from Payroll > Deductions.')
add_bullet('Deductions are automatically applied during payslip generation based on targeting rules.')
add_bullet('Loan instalment deductions are auto-created when a loan is approved (see Section 12).')

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 7. PAYSLIP GENERATION
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('7. Payslip Generation (Individual &amp; Batch)', level=1)

doc.add_heading('7.1 Individual Payslip Generation', level=2)
add_step(1, 'Go to Payroll > Payslips.')
add_step(2, 'Click the "Generate Payslip" button or navigate to the per-employee generate option.')
add_step(3, 'Select the Employee.')
add_step(4, 'Select the Start Date and End Date (pay period).')
add_step(5, 'Click "Generate". The system validates the contract, calculates all allowances/deductions, and creates a Draft payslip.')
add_step(6, 'You are redirected to the payslip detail view where you can see the full breakdown.')

doc.add_heading('7.2 Batch (Bulk) Payslip Generation', level=2)
add_step(1, 'Go to Payroll > Payslips.')
add_step(2, 'Click the "Bulk Generate" or "Batch Generate" button (typically near the top-right).')
add_step(3, 'In the form that opens:')
add_bullet('Select Employees: Choose one or more employees (or select by department/group).')
add_bullet('Select Start Date and End Date for the pay period.')
add_bullet('Optional: Enter a Batch Name / Group Name (e.g., "January 2026 - Monthly Staff").')
add_step(4, 'Click "Generate". The system creates payslips for all selected employees in a single operation.')
add_step(5, 'A success message shows the count, and you are redirected to the payslip list, grouped by batch name.')

doc.add_heading('7.3 What Happens During Calculation', level=2)
doc.add_paragraph(
    'When a payslip is generated, the system performs these steps internally:'
)
add_bullet('Reads the employee\'s active contract to get basic salary/wage.')
add_bullet('Calculates basic pay for the period (adjusts for unpaid leave).')
add_bullet('Applies all applicable allowances (fixed, percentage, attendance, shift, etc.) to arrive at Gross Pay.')
add_bullet('Applies pre-tax deductions (e.g., pension) to reduce taxable amount.')
add_bullet('Calculates Taxable Gross Pay.')
add_bullet('Applies tax deductions based on Filing Status + Tax Brackets.')
add_bullet('Applies post-tax deductions (e.g., garnishments, charity).')
add_bullet('Subtracts all deductions from Gross Pay to get Net Pay.')
add_bullet('Saves the payslip with full pay head data (breakdown of every component).')

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 8. PAYSLIP LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('8. Payslip Lifecycle (Draft \u2192 Review \u2192 Confirmed \u2192 Paid)', level=1)
doc.add_paragraph(
    'Every payslip follows a four-stage lifecycle that allows for review and approval before finalisation.'
)

add_table(
    ['Stage', 'Status Value', 'Meaning'],
    [
        ['1. Draft', 'draft', 'Initial state after generation. Payslip can be edited or deleted.'],
        ['2. Review Ongoing', 'review_ongoing', 'Under review by manager/HR. No further edits allowed without reverting.'],
        ['3. Confirmed', 'confirmed', 'Approved and final. Ready for payment processing.'],
        ['4. Paid', 'paid', 'Payment has been made. Final state.'],
    ]
)

doc.add_heading('8.1 Update Payslip Status', level=2)
add_step(1, 'Go to Payroll > Payslips.')
add_step(2, 'Find the payslip(s) you want to update.')
add_step(3, 'Click the status badge (e.g., "Draft") to advance it, or use the bulk status update dropdown.')
add_step(4, 'Alternatively, open the payslip detail view and change the status from the dropdown.')
add_step(5, 'Confirm the status change.')

doc.add_heading('8.2 Bulk Status Update', level=2)
add_step(1, 'From the Payslip list view, check the boxes for multiple payslips.')
add_step(2, 'Select the desired new status from the "Actions" dropdown (e.g., "Mark as Confirmed").')
add_step(3, 'Click "Apply" or "Update".')
add_step(4, 'All selected payslips are updated to the new status.')

add_note('Once a payslip is "Confirmed" or "Paid", it cannot be easily deleted. Ensure accuracy before advancing beyond "Draft".')

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 9. VIEWING, PDF, EMAIL
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('9. Viewing, PDF Download &amp; Email Delivery', level=1)

doc.add_heading('9.1 View a Payslip', level=2)
add_step(1, 'Go to Payroll > Payslips.')
add_step(2, 'Click on any payslip row to open the detail view.')
add_step(3, 'The detail view shows: Employee info, pay period, Basic Pay, each Allowance with amount, '
             'each Deduction with amount, Gross Pay, Total Deductions, and Net Pay.')
add_step(4, 'Employees can view their own payslips (role-based access).')

doc.add_heading('9.2 Download Payslip as PDF', level=2)
add_step(1, 'From the payslip detail view, click the "PDF" or "Download PDF" button.')
add_step(2, 'The system generates a PDF of the payslip, which is downloaded to your browser.')
add_step(3, 'You can print the PDF or share it manually.')

doc.add_heading('9.3 Email Payslip to Employee', level=2)
add_step(1, 'From the payslip list view, check one or more payslips.')
add_step(2, 'Select "Send Slip" or "Email Payslips" from the Actions dropdown.')
add_step(3, 'The system sends each employee their payslip via email (requires email server configuration).')
add_step(4, 'A confirmation message shows "Mail processing" - emails are sent asynchronously in the background.')

add_note('Email delivery requires an SMTP server to be configured in Horilla settings (Base > Email Configuration). '
         'If not configured, you will see an error message prompting you to set it up.')

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 10. PAYROLL DASHBOARD & REPORTING
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('10. Payroll Dashboard &amp; Reporting', level=1)

doc.add_heading('10.1 Dashboard Overview', level=2)
add_step(1, 'Go to Payroll > Dashboard.')
add_step(2, 'The dashboard displays:')
add_bullet('Total Paid amount for the selected month')
add_bullet('Total Confirmed amount')
add_bullet('Total Draft amount')
add_bullet('Employee chart: Payslip amounts by employee')
add_bullet('Department chart: Payslip amounts by department')
add_bullet('Contract Ending: List of contracts expiring soon')
add_bullet('Contribution Report: Employer vs employee contribution breakdown')

doc.add_heading('10.2 Filtering &amp; Grouping', level=2)
add_step(1, 'From Payroll > Payslips, use the filter side panel to narrow results.')
add_step(2, 'Filter by: Employee, Department, Job Position, Pay Period (start/end date), Status, Batch Name.')
add_step(3, 'Group by: Use the "Group By" dropdown to group payslips by Employee, Department, '
             'Status, Batch Name, or other fields.')

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 11. EXCEL EXPORT
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('11. Excel Export \u2013 Detailed Payslip Reports', level=1)

doc.add_heading('11.1 Basic Excel Export', level=2)
add_step(1, 'Go to Payroll > Payslips.')
add_step(2, 'Apply any desired filters.')
add_step(3, 'Click the "Export" button (Excel icon).')
add_step(4, 'Select the columns you want to include in the export.')
add_step(5, 'Click "Export". An Excel file is downloaded with multiple sheets containing:')
add_bullet('Employee-level breakdown')
add_bullet('Departmental totals')
add_bullet('Employer contribution summaries')
add_bullet('Contract ending reports')

doc.add_heading('11.2 Detailed Payslip Export', level=2)
add_step(1, 'From the Payslip list, click "Detailed Export" or navigate to the detailed export view.')
add_step(2, 'Select the specific columns and data points to include.')
add_step(3, 'The export includes:')
add_bullet('Employee details (name, department, position)')
add_bullet('Pay period dates')
add_bullet('Each allowance amount (by allowance name)')
add_bullet('Each deduction amount (by deduction name)')
add_bullet('Gross Pay, Total Deductions, Net Pay')
add_bullet('Employer contributions')
add_step(4, 'Click "Export" to download the Excel file.')

add_note('The Excel export is ideal for feeding payroll data into external accounting systems or for audit/review purposes.')

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 12. LOAN & ADVANCED SALARY
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('12. Loan &amp; Advanced Salary Management', level=1)

doc.add_heading('12.1 Create a Loan / Advanced Salary', level=2)
add_step(1, 'Go to Payroll > Loan / Advanced Salary.')
add_step(2, 'Click "Create Loan" or "Create Advanced Salary".')
add_step(3, 'Fill in the form:')
add_table(
    ['Field', 'Description'],
    [
        ['Type', 'Loan, Advanced Salary, or Penalty/Fine'],
        ['Title', 'A descriptive name (e.g., "Car Loan - John")'],
        ['Employee', 'Select the employee'],
        ['Amount (Loan Amount)', 'Total loan amount'],
        ['Provided Date', 'Date the loan was provided'],
        ['Total Installments', 'Number of installments to repay'],
        ['Installment Amount', 'Amount per installment (auto-calculated if blank)'],
        ['Installment Start Date', 'When the first deduction begins'],
    ]
)
add_step(4, 'Click "Save". The system automatically:')
add_bullet('Creates a Deduction record for each installment')
add_bullet('Links the deductions to the loan')
add_bullet('The deductions will be automatically applied during future payslip generation')

doc.add_heading('12.2 View Loan Installments', level=2)
add_step(1, 'Go to Payroll > Loan / Advanced Salary.')
add_step(2, 'Click on a loan record or the "View Installments" button.')
add_step(3, 'The installments view shows: Each installment date, amount, and whether it has been paid '
             '(linked to a payslip).')
add_step(4, 'You can edit individual installment amounts if needed.')

doc.add_heading('12.3 Settle a Loan', level=2)
add_step(1, 'Once all installments are paid, the loan status can be marked as "Settled".')
add_step(2, 'Check the "Settled" checkbox on the loan record.')
add_step(3, 'Save. The settled date is recorded automatically.')

doc.add_heading('12.4 Delete a Loan', level=2)
add_step(1, 'From the Loan list view, check the box(es) for the loan(s).')
add_step(2, 'Click "Delete".')
add_note('Loans that have payslips already generated against their installments cannot be deleted.')

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 13. REIMBURSEMENTS & ENCASHMENTS
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('13. Reimbursements &amp; Encashments', level=1)
doc.add_paragraph(
    'Three types of requests are handled: Reimbursement (expense claim), Leave Encashment '
    '(convert unused leave days to cash), and Bonus Point Encashment (redeem bonus points for cash).'
)

doc.add_heading('13.1 Create a Reimbursement', level=2)
add_step(1, 'Go to Payroll > Encashments & Reimbursements.')
add_step(2, 'Click "Create Request".')
add_step(3, 'Select Type: "Reimbursement".')
add_step(4, 'Fill in:')
add_bullet('Title: e.g., "Travel Expense - Client Meeting"')
add_bullet('Employee: The employee requesting reimbursement')
add_bullet('Allowance On: Date of the expense')
add_bullet('Amount: The amount to be reimbursed')
add_bullet('Attachment: Upload a receipt/invoice (required for reimbursements)')
add_bullet('Description: Optional notes')
add_step(5, 'Click "Save". The status is "Requested" by default.')

doc.add_heading('13.2 Create a Leave Encashment', level=2)
add_step(1, 'Go to Payroll > Encashments & Reimbursements > Create Request.')
add_step(2, 'Select Type: "Leave Encashment".')
add_step(3, 'Fill in:')
add_bullet('Title: e.g., "Annual Leave Encashment"')
add_bullet('Employee: The employee')
add_bullet('Leave Type: Select the leave type (e.g., "Annual Leave")')
add_bullet('Available Days to Encash: Number of available leave days to convert')
add_bullet('Carry Forward Days to Encash: Number of carry-forward days to convert')
add_step(4, 'The amount is auto-calculated based on the Encashment General Settings.')
add_step(5, 'Click "Save".')

doc.add_heading('13.3 Create a Bonus Point Encashment', level=2)
add_step(1, 'Go to Payroll > Encashments & Reimbursements > Create Request.')
add_step(2, 'Select Type: "Bonus Point Encashment".')
add_step(3, 'Fill in:')
add_bullet('Title: e.g., "Bonus Redemption"')
add_bullet('Employee: The employee')
add_bullet('Bonus Points: Number of bonus points to encash')
add_step(4, 'The amount is auto-calculated based on Encashment General Settings.')
add_step(5, 'Click "Save".')

doc.add_heading('13.4 Approve / Reject Requests', level=2)
add_step(1, 'Go to Payroll > Encashments & Reimbursements.')
add_step(2, 'Select one or more requests by checking the boxes.')
add_step(3, 'From the Actions dropdown, select "Approve" or "Reject".')
add_step(4, 'For leave encashments, the system automatically deducts the encashed days from the employee\'s leave balance.')
add_step(5, 'For reimbursements and encashments, an Allowance record is auto-created, '
             'so the amount is included in the next applicable payslip.')

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 14. ONE-TIME BONUSES & DEDUCTIONS
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('14. Adding One-Time / Ad-Hoc Bonuses &amp; Deductions to Payslips', level=1)

doc.add_heading('14.1 Add a Bonus to an Existing Payslip', level=2)
add_step(1, 'Go to Payroll > Payslips.')
add_step(2, 'Open the payslip you want to modify.')
add_step(3, 'Click "Add Bonus" or navigate to the bonus form.')
add_step(4, 'Select the Employee (pre-filled) and enter:')
add_bullet('Title: e.g., "Performance Bonus"')
add_bullet('Amount: The bonus amount')
add_bullet('One Time Date: Date of the bonus')
add_step(5, 'Save. The system regenerates the payslip with the bonus included.')

doc.add_heading('14.2 Add a One-Time Deduction to an Existing Payslip', level=2)
add_step(1, 'Open the payslip detail view.')
add_step(2, 'Click "Add Deduction".')
add_step(3, 'Enter the deduction details (title, amount, etc.).')
add_step(4, 'Save. The payslip is regenerated with the new deduction included.')

add_note('When you add a bonus or deduction to an existing payslip, the old payslip is deleted and '
         'a new one is generated with the updated calculations. This ensures the pay head data is always consistent.')

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 15. AUTO PAYSLIP GENERATION
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('15. Auto Payslip Generation Scheduling', level=1)
doc.add_paragraph(
    'Horilla can automatically generate payslips on a specified day each month, '
    'removing the need for manual generation.'
)

doc.add_heading('15.1 Configure Auto Generation', level=2)
add_step(1, 'Go to Payroll > Payslips (or Contract).')
add_step(2, 'Click the "Settings" icon and locate the Auto Payslip Generation section.')
add_step(3, 'Select the Generate Day (e.g., "1st" for the 1st of each month).')
add_step(4, 'Check "Auto Generate" to enable.')
add_step(5, 'If you have multiple companies, select the Company (or leave blank for all companies).')
add_step(6, 'Click "Save". A background scheduler will now automatically generate payslips on the specified day each month '
             'for all employees with active contracts.')

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 16. CONTRACT MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('16. Contract Management &amp; Bulk Operations', level=1)

doc.add_heading('16.1 Bulk Contract Status Update', level=2)
add_step(1, 'Go to Payroll > Contract.')
add_step(2, 'Filter or select the contracts you want to update.')
add_step(3, 'Check the boxes for the selected contracts.')
add_step(4, 'From the "Actions" dropdown, choose the new status (Active, Draft, Expired, Terminated).')
add_step(5, 'Click "Apply". The status of all selected contracts is updated.')

doc.add_heading('16.2 Export Contracts', level=2)
add_step(1, 'From Payroll > Contract, click "Export".')
add_step(2, 'Select the columns you want to export.')
add_step(3, 'Click "Export". The file downloads as an Excel spreadsheet.')

doc.add_heading('16.3 Bulk Delete Contracts', level=2)
add_step(1, 'Select the contract(s) you want to delete.')
add_step(2, 'From the Actions dropdown, choose "Delete Contracts".')
add_step(3, 'Confirm the deletion.')

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 17. MICROSOFT DYNAMICS INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('17. Microsoft Dynamics Integration Strategy', level=1)
doc.add_paragraph(
    'There is no pre-built connector between Horilla and Microsoft Dynamics. '
    'However, integration is achievable via Horilla\'s REST API. '
    'Below is the step-by-step approach for building the integration.'
)

doc.add_heading('17.1 Prerequisites', level=2)
add_bullet('Horilla REST API is available at /api/swagger/ (Swagger documentation)')
add_bullet('Authentication: JWT tokens (obtain via /api/auth/)')
add_bullet('Dynamics 365 Finance & Operations exposes its own OData/REST API')

doc.add_heading('17.2 Integration Workflow (Conceptual)', level=2)
add_step(1, 'Set up a middleware service (Python, Node.js, Azure Logic Apps, or similar).')
add_step(2, 'Configure scheduled synchronization jobs (daily or after each payroll run).')
add_step(3, 'Data flow - Dynamics to Horilla:')
add_bullet('Pull new/updated employee master data (IDs, names, departments, bank details).')
add_bullet('Pull organizational changes (new hires, terminations, transfers, promotions).')
add_bullet('Push updates into Horilla via the REST API.')
add_step(4, 'Process payroll in Horilla as normal (see Section 7).')
add_step(5, 'Data flow - Horilla to Dynamics:')
add_bullet('Extract payroll results via Horilla API (payslips, per-employee breakdowns).')
add_bullet('Extract employer contribution summaries.')
add_bullet('Transform data into Dynamics-compatible format.')
add_bullet('Post journal entries to Dynamics 365 Finance (General Ledger).')
add_step(6, 'Handle errors and mismatches via logging and alerts.')

add_table(
    ['Data Type', 'Direction', 'Description'],
    [
        ['Employee Master', 'Dynamics \u2192 Horilla', 'Names, IDs, departments, bank details'],
        ['Organisational Changes', 'Dynamics \u2192 Horilla', 'New hires, terminations, transfers'],
        ['Payroll Results', 'Horilla \u2192 Dynamics', 'Gross pay, deductions, net pay per employee'],
        ['Employer Contributions', 'Horilla \u2192 Dynamics', 'Employer tax/benefit contributions for GL'],
        ['Leave & Attendance', 'Both ways', 'Leave balances, attendance records'],
    ]
)

doc.add_heading('17.3 REST API Endpoints (Key Payroll Endpoints)', level=2)
add_code('GET    /api/payroll/contracts/           # List all contracts')
add_code('POST   /api/payroll/contracts/           # Create a contract')
add_code('GET    /api/payroll/allowances/           # List all allowances')
add_code('GET    /api/payroll/deductions/           # List all deductions')
add_code('GET    /api/payroll/payslips/             # List all payslips')
add_code('GET    /api/payroll/loans/                # List all loans')
add_code('POST   /api/payroll/payslips/generate/    # Trigger payslip generation')

add_note('Full API documentation is available at '
         'http(s)://your-horilla-instance/api/swagger/')

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# APPENDIX: PERMISSIONS REFERENCE
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('Appendix A: Payroll Permissions Reference', level=1)
doc.add_paragraph(
    'The following permissions control access to payroll actions. '
    'Assign these to user roles/groups in Horilla > Settings > Permissions.'
)

add_table(
    ['Permission Codename', 'Description'],
    [
        ['payroll.view_contract', 'View contracts'],
        ['payroll.add_contract', 'Create contracts'],
        ['payroll.change_contract', 'Edit contracts'],
        ['payroll.delete_contract', 'Delete contracts'],
        ['payroll.view_allowance', 'View allowances'],
        ['payroll.add_allowance', 'Create allowances'],
        ['payroll.change_allowance', 'Edit allowances'],
        ['payroll.delete_allowance', 'Delete allowances'],
        ['payroll.view_deduction', 'View deductions'],
        ['payroll.add_deduction', 'Create deductions'],
        ['payroll.change_deduction', 'Edit deductions'],
        ['payroll.delete_deduction', 'Delete deductions'],
        ['payroll.view_payslip', 'View payslips'],
        ['payroll.add_payslip', 'Generate payslips'],
        ['payroll.change_payslip', 'Edit payslips / change status'],
        ['payroll.delete_payslip', 'Delete payslips'],
        ['payroll.view_loanaccount', 'View loan accounts'],
        ['payroll.add_loanaccount', 'Create loans'],
        ['payroll.change_loanaccount', 'Edit loans'],
        ['payroll.delete_loanaccount', 'Delete loans'],
        ['payroll.view_reimbursement', 'View reimbursements'],
        ['payroll.add_reimbursement', 'Create reimbursements'],
        ['payroll.change_reimbursement', 'Approve/reject reimbursements'],
        ['payroll.delete_reimbursement', 'Delete reimbursements'],
        ['payroll.view_filingstatus', 'View filing statuses'],
        ['payroll.add_filingstatus', 'Create filing statuses'],
        ['payroll.change_filingstatus', 'Edit filing statuses'],
        ['payroll.delete_filingstatus', 'Delete filing statuses'],
        ['payroll.view_taxbracket', 'View tax brackets'],
        ['payroll.add_taxbracket', 'Create tax brackets'],
        ['payroll.change_taxbracket', 'Edit tax brackets'],
        ['payroll.delete_taxbracket', 'Delete tax brackets'],
    ]
)

# ── Final touch ──────────────────────────────────────────────────────────
doc.add_paragraph('')
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('\u2014 End of Document \u2014')
run.bold = True
run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

# ═══════════════════════════════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════════════════════════════
output_path = r'C:\Users\tyseg\hrm\Horilla_Payroll_Technical_HowTo_Guide.docx'
doc.save(output_path)
print(f'Document saved to: {output_path}')
