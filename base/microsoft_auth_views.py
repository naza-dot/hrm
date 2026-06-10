"""
Microsoft OAuth authentication views for Horilla HRM
"""

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from urllib.parse import urlencode
import requests
from employee.models import Employee
from .models import Company, MicrosoftSSOConfig


def _get_microsoft_sso_config(request):
    """Load the active MicrosoftSSOConfig from the database.

    Tries the current user's company first, then falls back to any active
    config.  Returns ``(config, tenant_id, client_id, client_secret)``
    where all values are strings (empty if not configured).
    """
    try:
        company = request.user.employee_get.employee_work_info.company_id
        config = MicrosoftSSOConfig.objects.filter(
            company_id=company, is_active=True
        ).first()
    except Exception:
        config = MicrosoftSSOConfig.objects.filter(is_active=True).first()
    if not config:
        config = MicrosoftSSOConfig.objects.filter(is_active=True).first()
    tenant_id = config.tenant_id if config else ""
    client_id = config.client_id if config else ""
    client_secret = config.client_secret if config else ""
    return config, tenant_id, client_id, client_secret


def _compute_redirect_uri(request):
    scheme = 'https'
    if settings.DEBUG:
        scheme = getattr(settings, 'MICROSOFT_AUTH_SCHEME', 'https')
    site_url = getattr(settings, "SITE_URL", None)
    if site_url:
        return f"{site_url.rstrip('/')}/login-microsoft/callback/"
    return request.build_absolute_uri('/login-microsoft/callback/').replace(
        'http://', f'{scheme}://'
    )


def microsoft_auth_login(request):
    """Handle Microsoft SSO settings form and redirect to Microsoft OAuth.

    On POST the client credentials are stored in the
    :class:`MicrosoftSSOConfig` model.  On a GET request the user is
    redirected to the Microsoft OAuth flow using credentials from the
    database only (never from environment variables).
    """
    redirect_uri = _compute_redirect_uri(request)

    if request.method == "POST":
        client_id = request.POST.get("client_id")
        client_secret = request.POST.get("client_secret")
        tenant_id = request.POST.get("tenant_id")
        try:
            company = request.user.employee_get.employee_work_info.company_id
        except Exception:
            company = None
        if not company:
            company = Company.objects.first()
        if not company:
            company, __ = Company.objects.get_or_create(
                company="Default", address="", country="", state="", city="", zip=""
            )
        MicrosoftSSOConfig.objects.update_or_create(
            company_id=company,
            defaults={
                "client_id": client_id,
                "client_secret": client_secret,
                "tenant_id": tenant_id,
                "redirect_uri": redirect_uri,
                "is_active": True,
            },
        )
        messages.success(request, _("Microsoft SSO settings updated."))
        if request.META.get("HTTP_HX_REQUEST"):
            return HttpResponse()
        return redirect("microsoft-sso-settings")

    # GET: initiate OAuth flow using DB-stored credentials
    config, tenant_id, client_id, client_secret = _get_microsoft_sso_config(request)

    if not client_id or not tenant_id:
        messages.error(
            request,
            _("Microsoft SSO is not configured. Please configure it in Settings → Microsoft."),
        )
        return redirect("microsoft-sso-settings")

    auth_url = "https://login.microsoftonline.com/{}/oauth2/v2.0/authorize".format(
        tenant_id
    )

    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'response_mode': 'query',
        'scope': 'openid profile email',
        'state': request.session.session_key or 'microsoft_auth_state'
    }

    request.session['microsoft_auth_state'] = params['state']

    auth_url = "https://login.microsoftonline.com/{}/oauth2/v2.0/authorize?{}".format(
        tenant_id,
        urlencode(params)
    )
    return redirect(auth_url)


def microsoft_auth_callback(request):
    """
    Handle Microsoft OAuth callback
    """
    state = request.GET.get('state')
    stored_state = request.session.get('microsoft_auth_state')
    
    if not state or state != stored_state:
        messages.error(request, _("Invalid authentication state."))
        return redirect('login')
    
    code = request.GET.get('code')
    if not code:
        error = request.GET.get('error', 'unknown_error')
        messages.error(request, _("Authentication failed: {}").format(error))
        return redirect('login')
    
    config, tenant_id, client_id, client_secret = _get_microsoft_sso_config(request)
    if not client_id or not tenant_id:
        messages.error(request, _("Microsoft SSO is not configured."))
        return redirect('login')
    
    try:
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        
        scheme = 'https'
        if settings.DEBUG:
            scheme = getattr(settings, 'MICROSOFT_AUTH_SCHEME', 'https')
        
        redirect_uri = request.build_absolute_uri('/login-microsoft/callback/').replace('http://', f'{scheme}://')
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_info = token_response.json()
        
        # Get user information from Microsoft Graph API
        access_token = token_info.get('access_token')
        user_info_url = 'https://graph.microsoft.com/v1.0/me'
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        user_response = requests.get(user_info_url, headers=headers)
        user_response.raise_for_status()
        user_info = user_response.json()
        
        # Get user's email
        email = user_info.get('mail') or user_info.get('userPrincipalName')
        if not email:
            messages.error(request, _("Could not retrieve email from Microsoft account."))
            return redirect('login')
        
        # Find or create user
        user = None
        try:
            # Try to find existing user by email
            user = User.objects.get(email=email)
            
            # For existing users, ensure Employee record exists
            try:
                employee = Employee.objects.get(employee_user_id=user)
            except Employee.DoesNotExist:
                # Create Employee record for existing user
                display_name = user_info.get('displayName', email.split('@')[0])
                employee = Employee.objects.create(
                    employee_user_id=user,
                    employee_first_name=user.first_name or display_name.split()[0] if display_name else email.split('@')[0],
                    employee_last_name=user.last_name or ' '.join(display_name.split()[1:]) if display_name and len(display_name.split()) > 1 else '',
                    email=email,
                    phone='0000000000',  # Required field - placeholder value
                    is_active=True
                )
                employee.save()
                
        except User.DoesNotExist:
            # Create new user if not found
            display_name = user_info.get('displayName', email.split('@')[0])
            username = email.split('@')[0]
            
            # Ensure unique username
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=display_name.split()[0] if display_name else '',
                last_name=' '.join(display_name.split()[1:]) if display_name and len(display_name.split()) > 1 else ''
            )
            
            # Set a random password (user will use Microsoft to login)
            user.set_unusable_password()
            user.save()
            
            # Create Employee record for the new user
            try:
                employee = Employee.objects.create(
                    employee_user_id=user,
                    employee_first_name=user.first_name or email.split('@')[0],
                    employee_last_name=user.last_name or '',
                    email=email,
                    phone='0000000000',  # Required field - placeholder value
                    is_active=True
                )
                employee.save()
            except Exception as e:
                # If employee creation fails, delete the user and show error
                user.delete()
                raise Exception(f"Failed to create employee record: {str(e)}")
        
        # Verify Employee record exists before logging in
        try:
            employee = Employee.objects.get(employee_user_id=user)
        except Employee.DoesNotExist:
            messages.error(request, _("Failed to create employee record for user."))
            return redirect('login')
        
        # Log in the user with explicit backend
        login(request, user, backend='microsoft_auth.backends.MicrosoftAuthenticationBackend')
        
        # Clean up session
        if 'microsoft_auth_state' in request.session:
            del request.session['microsoft_auth_state']
        
        messages.success(request, _("Successfully logged in with Microsoft account."))
        
        # Redirect to intended page or home
        next_url = request.GET.get('next') or request.session.get('next') or '/'
        if 'next' in request.session:
            del request.session['next']
        
        return redirect(next_url)
        
    except requests.exceptions.RequestException as e:
        messages.error(request, _("Failed to connect to Microsoft services: {}").format(str(e)))
        return redirect('login')
    except Exception as e:
        messages.error(request, _("An error occurred during Microsoft authentication: {}").format(str(e)))
        return redirect('login')
