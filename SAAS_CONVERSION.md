# SAAS Conversion Implementation Guide

## Goal
Formalize tenant isolation so organizations cannot see each other's data. Establish two admin roles:
- **External Admin (SaaS Admin)** — global overview of all organizations; assigns module features to each company.
- **Internal Admin (Company Admin)** — works only within their own company, restricted to the features the External Admin granted.

## Current State
The project already has a multi-company layer:
- `HorillaCompanyManager` — auto-filters querysets by `selected_company` session variable
- `CompanyMiddleware` — injects `company_filter` Q objects on every model
- Company switcher UI — allows switching to "All Companies"
- `EmployeeWorkInformation.company_id` — is the primary tenant FK

**The problem:** Any user can switch to "All Companies" and see all tenants' data. There is no enforcement.

---

## Implementation Steps

### 1. Add a `is_saas_admin` flag to User
**File:** `base/models.py` (near line 1902 where `is_new_employee` is added)

```python
User.add_to_class("is_saas_admin", models.BooleanField(default=False))
```

This flag explicitly marks a user as the global SaaS admin (distinct from org-level roles). Only this flag + `is_superuser` can bypass tenant isolation.

---

### 2. Restrict the "All Companies" company switcher option
**File:** `base/context_processors.py` — function `get_companies()`

Wrap the "All Companies" option so it only appears when `request.user.is_saas_admin`:

```python
companies = []
if request.user.is_authenticated and request.user.is_saas_admin:
    companies.append([
        "all",
        "All Company",
        "https://ui-avatars.com/api/?name=All+Company&background=random",
        False,
    ])
# then add per-company entries for the user's org
```

This is the **primary UX enforcement** — non-admin users literally cannot select "All Companies".

---

### 3. Enforce tenant isolation in `HorillaCompanyManager.get_queryset()`
**File:** `base/horilla_company_manager.py`

Modify `get_queryset()` to **default to the user's own company** (never fall back to unfiltered) for non-saas-admin users:

```python
def get_queryset(self):
    queryset = super().get_queryset()
    request = getattr(_thread_locals, "request", None)
    if request is None:
        return queryset

    user = request.user
    if user.is_authenticated and not user.is_saas_admin:
        # Force-filter to the user's own company
        try:
            user_company = user.employee_get.employee_work_info.company_id
            if user_company:
                return queryset.filter(
                    self.model.company_filter if hasattr(self.model, 'company_filter') 
                    else Q(company_id=user_company)
                )
        except AttributeError:
            pass

    # Only saas_admin can use the session-based "all" or specific company selection
    selected_company = request.session.get("selected_company")
    if selected_company and selected_company != "all":
        try:
            queryset = queryset.filter(self.model.company_filter)
        except Exception:
            pass
    elif selected_company != "all" or not user.is_saas_admin:
        # Fall back to user's own company
        try:
            user_company = user.employee_get.employee_work_info.company_id
            if user_company:
                return queryset.filter(company_id=user_company)
        except AttributeError:
            pass

    return queryset
```

---

### 4. Restrict `CompanyMiddleware` for non-admin users
**File:** `base/middleware.py`

In the `__call__` method and `_set_company_session`, force non-saas-admin users to their own company. Never allow `selected_company = "all"` for non-saas-admin:

```python
def __call__(self, request):
    if getattr(request, "user", False) and not request.user.is_anonymous:
        if request.user.is_saas_admin:
            company_id = self._get_company_id(request)
        else:
            # Force to user's own company
            try:
                company = request.user.employee_get.employee_work_info.company_id
                company_id = company
            except AttributeError:
                company_id = None
        self._set_company_session(request, company_id)
        # ... rest of method
```

---

### 5. Create a superadmin-only view to browse all organizations
**File:** `base/views.py`

Add a simple view (protected by `is_saas_admin` check) that lists all companies with employee counts:

```python
@login_required
def saas_admin_dashboard(request):
    if not request.user.is_saas_admin:
        return render(request, "no_perm.html")
    companies = Company.objects.all()
    return render(request, "saas_admin_dashboard.html", {"companies": companies})
```

**File:** `base/urls.py` — add route:

```python
path("saas-admin/dashboard", saas_admin_dashboard, name="saas-admin-dashboard"),
```

**File:** Create minimal template `templates/saas_admin_dashboard.html` showing company list with links to switch to that company.

---

### 6. Make `update_selected_company` respect SaaS isolation
**File:** `base/context_processors.py` — `update_selected_company()`

Add a guard at the top:

```python
@login_required
@hx_request_required
def update_selected_company(request):
    if not request.user.is_saas_admin and request.GET.get("company_id") == "all":
        messages.error(request, _("You don't have permission to view all companies."))
        return HttpResponse(status=403)

    if not request.user.is_saas_admin:
        # Force to own company
        user = request.user.employee_get
        user_company = getattr(getattr(user, "employee_work_info", None), "company_id", None)
        if str(request.GET.get("company_id")) != str(user_company.id if user_company else None):
            messages.error(request, _("You can only switch to your own company."))
            return HttpResponse(status=403)
    # ... rest of existing logic
```

---

### 7. API isolation
**File:** `horilla_api/middleware.py` (and relevant API views)

Apply the same `is_saas_admin` guard. For DRF, create a custom permission class:

```python
from rest_framework.permissions import BasePermission

class IsSaaSAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_saas_admin
```

For API views that list cross-tenant data, use `IsSaaSAdmin` or filter to the user's own company.

---

### 8. Seed the first SaaS admin
In your deployment/initialization script, ensure the first superuser created via `createsuperuser` has `is_saas_admin=True`. Or add a data migration.

---

### 9. Define the two admin roles

| Role | Scope | Responsibilities |
|------|-------|-----------------|
| **External Admin** (`is_saas_admin=True`) | All companies | Assign features to companies, view any company's data, create/manage companies |
| **Internal Admin** (`is_saas_admin=False`, has company-level permissions) | Own company only | Manage users, roles, permissions within their org; use only the modules granted to their company |

The `is_saas_admin` flag (step 1) is the single discriminator. An Internal Admin is simply a user within a company who holds Django admin-level permissions — but those permissions are scoped to their own company by the tenant isolation in steps 2-4.

---

### 10. Feature/Module assignment model

**File:** `base/models.py`

Add a model that tracks which features (Django apps/modules) are enabled per company:

```python
class CompanyFeature(models.Model):
    """
    Maps which modules/features are enabled for each company.
    Only the External Admin can modify this.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="enabled_features")
    feature = models.CharField(max_length=100)          # e.g. "attendance", "leave", "payroll", "recruitment"
    is_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("company", "feature")
        verbose_name = "Company Feature"
        verbose_name_plural = "Company Features"

    def __str__(self):
        return f"{self.company.company} - {self.feature}: {'Enabled' if self.is_enabled else 'Disabled'}"
```

**Seed data:** Define the canonical list of feature keys (matching your Django app labels):

```python
HORILLA_FEATURES = [
    "attendance",
    "leave",
    "payroll",
    "recruitment",
    "onboarding",
    "offboarding",
    "pms",
    "asset",
    "helpdesk",
    "project",
    "biometric",
    "geofencing",
]
```

When a new company is created, auto-create a `CompanyFeature` row for every feature (default `is_enabled=False`):

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Company)
def create_company_features(sender, instance, created, **kwargs):
    if created:
        for feature in HORILLA_FEATURES:
            CompanyFeature.objects.create(company=instance, feature=feature, is_enabled=False)
```

---

### 11. Feature gating middleware

**File:** `base/middleware.py` (or a new `saas_middleware.py`)

Add middleware that attaches the enabled feature set to the request so all views/templates can check it:

```python
class FeatureGateMiddleware:
    """
    Attaches the list of enabled features for the current company to the request.
    Non-admin users cannot access disabled features.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, "user", False) and request.user.is_authenticated:
            if not request.user.is_saas_admin:
                try:
                    company = request.user.employee_get.employee_work_info.company_id
                    enabled = CompanyFeature.objects.filter(
                        company=company, is_enabled=True
                    ).values_list("feature", flat=True)
                    request.enabled_features = list(enabled)
                except AttributeError:
                    request.enabled_features = []
            else:
                # External Admin sees everything
                request.enabled_features = HORILLA_FEATURES
        else:
            request.enabled_features = []

        response = self.get_response(request)
        return response
```

Register it in `horilla/horilla_middlewares.py`:

```python
MIDDLEWARE = [
    # ... existing middleware ...
    "base.middleware.FeatureGateMiddleware",
    # ...
]
```

---

### 12. Feature gate utility (view-level enforcement)

**File:** `horilla/decorators.py`

Add a decorator to block access to views for disabled features:

```python
@decorator_with_arguments
def feature_required(function, feature_key):
    """
    Decorator that blocks access if the current company does not have
    the given feature enabled. Skipped for External Admin.
    """
    def _function(request, *args, **kwargs):
        if request.user.is_saas_admin:
            return function(request, *args, **kwargs)
        enabled = getattr(request, "enabled_features", [])
        if feature_key in enabled:
            return function(request, *args, **kwargs)
        return render(request, "no_perm.html")
    return _function
```

Apply it to each module's views. For example, in `attendance/views.py`:

```python
@feature_required("attendance")
def some_attendance_view(request):
    ...
```

---

### 13. Feature gate in templates (UI-level hiding)

**File:** `base/context_processors.py`

Add a context processor that exposes enabled features to all templates:

```python
def enabled_features(request):
    return {"enabled_features": getattr(request, "enabled_features", [])}
```

Register it in `horilla/settings.py`:

```python
TEMPLATES[0]["OPTIONS"]["context_processors"].append(
    "base.context_processors.enabled_features"
)
```

Then in any base template (e.g. the sidebar/nav), conditionally render navigation items:

```django
{% if "attendance" in enabled_features %}
    <li><a href="{% url 'attendance-dashboard' %}">Attendance</a></li>
{% endif %}
{% if "payroll" in enabled_features %}
    <li><a href="{% url 'payroll-dashboard' %}">Payroll</a></li>
{% endif %}
```

---

### 14. External Admin: feature assignment dashboard

**File:** `base/views.py`

A view where the External Admin sees all companies and toggles their features:

```python
@login_required
def saas_admin_company_features(request, company_id):
    if not request.user.is_saas_admin:
        return render(request, "no_perm.html")
    company = Company.objects.get(id=company_id)
    features = CompanyFeature.objects.filter(company=company)
    if request.method == "POST":
        for feature in features:
            key = f"feature_{feature.id}"
            feature.is_enabled = key in request.POST
            feature.save()
        messages.success(request, _("Features updated successfully."))
        return redirect("saas-admin-company-features", company_id=company.id)
    return render(request, "saas_admin_company_features.html", {
        "company": company,
        "features": features,
    })
```

**File:** `base/urls.py`

```python
path(
    "saas-admin/company/<int:company_id>/features",
    saas_admin_company_features,
    name="saas-admin-company-features",
),
```

**File:** `templates/saas_admin_company_features.html`

```django
{% extends "base.html" %}
{% block content %}
<h2>Features for {{ company.company }}</h2>
<form method="post">
  {% csrf_token %}
  <table>
    {% for feature in features %}
    <tr>
      <td>{{ feature.get_feature_display }}</td>
      <td><input type="checkbox" name="feature_{{ feature.id }}" {% if feature.is_enabled %}checked{% endif %}></td>
    </tr>
    {% endfor %}
  </table>
  <button type="submit">Save</button>
</form>
{% endblock %}
```

---

### 15. Internal Admin: company-scoped permission management

The Internal Admin manages their org using existing Django permissions, but scoped to their own company by the tenant isolation. No special code is needed beyond what is already in place — the `HorillaCompanyManager` and `CompanyMiddleware` automatically scope all data.

To designate an Internal Admin, the External Admin (or the Internal Admin themselves, if granted) assigns Django permissions through the existing admin interface. The key difference is:

- The Internal Admin **never** sees "All Companies" in the company switcher.
- The Internal Admin **never** sees navigation items for features their company doesn't have.
- All querysets are automatically scoped to the Internal Admin's company.

---

## Full flow diagram

```
┌──────────────────────────────────────────────────────────────┐
│                   External Admin (SaaS Admin)                │
│  ┌─────────────────┐  ┌──────────────────────────────────┐   │
│  │  Company List    │  │  Company Feature Assignment     │   │
│  │  ┌─────────────┐ │  │  ┌──────────┐ ┌──────────┐    │   │
│  │  │ Company A   │ │  │  │Attendance│ │  Leave   │    │   │
│  │  │ Company B   │ │  │  │ Payroll  │ │Recruitment│   │   │
│  │  │ Company C   │ │  │  └──────────┘ └──────────┘    │   │
│  │  └─────────────┘ │  └──────────────────────────────────┘   │
│  └─────────────────┘                                          │
│  Can view ANY company's data (selected_company = "all")       │
└──────────────────────────────────────────────────────────────┘
                          │
                          │ assigns features
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                   Per-Company Tenant                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │             Internal Admin (Company Admin)            │    │
│  │  ┌─────────────┐  ┌──────────────────────────────┐   │    │
│  │  │  Users       │  │  Permissions (Django auth)   │   │    │
│  │  │  Roles       │  │  Scoped to own company       │   │    │
│  │  │  Employees   │  │  Only enabled features shown │   │    │
│  │  └─────────────┘  └──────────────────────────────┘   │    │
│  │                                                       │    │
│  │  Can ONLY see their own company's data               │    │
│  │  Can ONLY use features granted by External Admin     │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  CompanyFeature table:                                        │
│  ┌─────────────┬──────────┬───────────┐                     │
│  │ feature     │ enabled  │ accessed? │                     │
│  ├─────────────┼──────────┼───────────┤                     │
│  │ attendance  │ True     │ ✓         │                     │
│  │ leave       │ True     │ ✓         │                     │
│  │ payroll     │ False    │ ✗ blocked │                     │
│  │ recruitment │ False    │ ✗ blocked │                     │
│  └─────────────┴──────────┴───────────┘                     │
└──────────────────────────────────────────────────────────────┘
```

---

## Summary of Changes

| File | Change |
|------|--------|
| `base/models.py` | Add `is_saas_admin` flag to User; add `CompanyFeature` model; add signal to auto-create features per company |
| `base/horilla_company_manager.py` | Default to user's own company for non-admin |
| `base/middleware.py` | Force company to user's own for non-admin; add `FeatureGateMiddleware` |
| `base/context_processors.py` | Hide "All Companies", guard `update_selected_company`; add `enabled_features` context processor |
| `base/views.py` | Add `saas_admin_dashboard` view; add `saas_admin_company_features` view |
| `base/urls.py` | Add routes for dashboard and per-company feature assignment |
| `templates/saas_admin_dashboard.html` | Company list template for External Admin |
| `templates/saas_admin_company_features.html` | Feature toggle form per company |
| `horilla/decorators.py` | Add `feature_required` decorator for view-level gating |
| `horilla/horilla_middlewares.py` | Register `FeatureGateMiddleware` |
| `horilla/settings.py` | Register `enabled_features` context processor |
| `horilla_api/middleware.py` | API permission class for admin |

---

## Architecture Diagram

```
                    ┌──────────────────────────────────────────┐
                    │           External Admin (SaaS)          │
                    │  ┌────────────────────────────────────┐  │
                    │  │  saas_admin_dashboard              │  │
                    │  │  saas_admin_company_features       │  │
                    │  │  selected_company = "all"          │  │
                    │  │  is_saas_admin = True              │  │
                    │  └────────────────────────────────────┘  │
                    └──────────────┬───────────────────────────┘
                                   │ assigns features
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Django Request Pipeline                     │
│                                                                  │
│  ┌──────────┐    ┌──────────────────┐    ┌───────────────────┐  │
│  │  Request  │───▶│ FeatureGate      │───▶│ CompanyMiddleware │  │
│  └──────────┘    │ Middleware        │    │                   │  │
│                  │ └─ checks         │    │ └─ if !saas_admin │  │
│                  │    CompanyFeature │    │    → own company  │  │
│                  │    for current    │    └───────────────────┘  │
│                  │    company        │           │               │
│                  │ └─ sets           │           ▼               │
│                  │    enabled_features│   ┌───────────────────┐  │
│                  │    on request      │   │ HorillaCompany    │  │
│                  └──────────────────┘   │ Manager           │  │
│                                         │ └─ auto-filters   │  │
│                                         │    queryset by    │  │
│                                         │    company        │  │
│                                         └───────────────────┘  │
│                                                    │            │
│                                                    ▼            │
│                                         ┌───────────────────┐  │
│                                         │  View + Decorator │  │
│                                         │  @feature_required│  │
│                                         │  checks feature   │  │
│                                         │  in enabled list  │  │
│                                         └───────────────────┘  │
│                                                    │            │
│                                                    ▼            │
│                                         ┌───────────────────┐  │
│                                         │  Template         │  │
│                                         │  {% if "attendance"│  │
│                                         │  in enabled_      │  │
│                                         │  features %}      │  │
│                                         └───────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  Internal Admin ─── sees only own company's data        │     │
│  │                  ─── sees only enabled features in UI   │     │
│  │                  ─── blocked at view layer otherwise    │     │
│  └─────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```
