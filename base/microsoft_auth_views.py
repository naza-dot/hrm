"""
Microsoft OAuth authentication views for Horilla HRM
"""

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from urllib.parse import urlencode
import requests
from employee.models import Employee


def microsoft_auth_login(request):
    """
    Redirect user to Microsoft OAuth login page
    """
    if not settings.MICROSOFT_AUTH_CLIENT_ID:
        messages.error(request, _("Microsoft authentication is not configured."))
        return redirect('login')
    
    # Microsoft OAuth authorization URL
    auth_url = "https://login.microsoftonline.com/{}/oauth2/v2.0/authorize".format(
        settings.MICROSOFT_AUTH_TENANT_ID
    )
    
    # OAuth parameters
    # Use HTTPS scheme for redirect URI (can be overridden with env var for development)
    scheme = 'https'  # Default to HTTPS for production
    if settings.DEBUG:
        # In debug mode, allow HTTP scheme override
        scheme = getattr(settings, 'MICROSOFT_AUTH_SCHEME', 'https')
    
    redirect_uri = request.build_absolute_uri('/login-microsoft/callback/').replace('http://', f'{scheme}://')
    params = {
        'client_id': settings.MICROSOFT_AUTH_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'response_mode': 'query',
        'scope': 'openid profile email',
        'state': request.session.session_key or 'microsoft_auth_state'
    }
    
    # Store state in session for security
    request.session['microsoft_auth_state'] = params['state']
    
    # Redirect to Microsoft OAuth
    return redirect(f"{auth_url}?{urlencode(params)}")


def microsoft_auth_callback(request):
    """
    Handle Microsoft OAuth callback
    """
    # Verify state for security
    state = request.GET.get('state')
    stored_state = request.session.get('microsoft_auth_state')
    
    if not state or state != stored_state:
        messages.error(request, _("Invalid authentication state."))
        return redirect('login')
    
    # Get authorization code
    code = request.GET.get('code')
    if not code:
        error = request.GET.get('error', 'unknown_error')
        messages.error(request, _("Authentication failed: {}").format(error))
        return redirect('login')
    
    try:
        # Exchange authorization code for access token
        token_url = f"https://login.microsoftonline.com/{settings.MICROSOFT_AUTH_TENANT_ID}/oauth2/v2.0/token"
        
        # Use HTTPS scheme for redirect URI (can be overridden with env var for development)
        scheme = 'https'  # Default to HTTPS for production
        if settings.DEBUG:
            # In debug mode, allow HTTP scheme override
            scheme = getattr(settings, 'MICROSOFT_AUTH_SCHEME', 'https')
        
        redirect_uri = request.build_absolute_uri('/login-microsoft/callback/').replace('http://', f'{scheme}://')
        token_data = {
            'client_id': settings.MICROSOFT_AUTH_CLIENT_ID,
            'client_secret': settings.MICROSOFT_AUTH_CLIENT_SECRET,
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
                    phone='',  # Empty phone - can be filled later
                    is_active=True
                )
                employee.save()
            except Exception as e:
                # If employee creation fails, delete the user and show error
                user.delete()
                raise Exception(f"Failed to create employee record: {str(e)}")
        
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
