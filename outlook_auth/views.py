"""
outlook_auth/views.py
"""

import logging
from datetime import datetime

from django.contrib import messages
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from requests_oauthlib import OAuth2Session

from horilla.decorators import login_required, permission_required
from outlook_auth import models

logger = logging.getLogger(__name__)


@login_required
@permission_required("outlook_auth.add_azureapi")
def outlook_login(request):
    """
    outlook login
    """
    selected_company = request.session.get("selected_company")
    if not selected_company or selected_company == "all":
        api = models.AzureApi.objects.filter(is_primary=True).first()
    else:
        api = models.AzureApi.objects.filter(company=selected_company).first()

    if not api:
        messages.info(request, "Not configured outlook")
    oauth = OAuth2Session(
        api.outlook_client_id,
        redirect_uri=api.outlook_redirect_uri,
        scope=["Mail.Send", "offline_access"],
    )
    authorization_url, state = oauth.authorization_url(api.outlook_authorization_url)

    api.oauth_state = state
    api.save()
    cache.set("oauth_state", state)
    return redirect(authorization_url)


def refresh_outlook_token(api: models.AzureApi):
    """
    Refresh Outlook token
    """
    oauth = OAuth2Session(
        api.outlook_client_id,
        token=api.token,
        auto_refresh_kwargs={
            "client_id": api.outlook_client_id,
            "client_secret": api.outlook_client_secret,
        },
        auto_refresh_url=api.outlook_token_url,
    )
    new_token = oauth.refresh_token(
        api.outlook_token_url,
        refresh_token=api.token["refresh_token"],
        client_id=api.outlook_client_id,
        client_secret=api.outlook_client_secret,
    )
    api.token = new_token
    api.last_refreshed = datetime.now()
    api.save()
    return api


@login_required
@permission_required("outlook_auth.change_azureapi")
def refresh_token(request, pk, *args, **kwargs):
    """
    outlook_freshe
    """
    api = models.AzureApi.objects.get(pk=pk)
    old_token = api.token.get("access_token")
    api = refresh_outlook_token(api)
    if api.token.get("access_token") == old_token:
        messages.info(request, _("Token not refreshed, Login required"))
    else:
        messages.success(request, _("Token refreshed successfully"))

    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required
@permission_required("outlook_auth.change_azureapi")
def outlook_callback(request):
    """
    outlook callback
    """
    selected_company = request.session.get("selected_company")
    if not selected_company or selected_company == "all":
        api = models.AzureApi.objects.filter(is_primary=True).first()
    else:
        api = models.AzureApi.objects.filter(company=selected_company).first()

    state = api.oauth_state

    oauth = OAuth2Session(
        api.outlook_client_id,
        state=state,
        redirect_uri=api.outlook_redirect_uri,
    )

    authorization_response_uri = request.build_absolute_uri()
    authorization_response_uri = authorization_response_uri.replace(
        "http://", "https://"
    )
    api.last_refreshed = datetime.now()
    token = oauth.fetch_token(
        api.outlook_token_url,
        client_secret=api.outlook_client_secret,
        authorization_response=authorization_response_uri,  # Use the modified URI
    )
    api.token = token
    api.save()

    return redirect("/")


def send_outlook_email(request, email_data=None):
    """
    Send email via Microsoft Graph API.
    Returns (response, email_data) on success, (None, email_data) on failure.
    """
    logger.info("send_outlook_email called")
    selected_company = None
    if request:
        selected_company = request.session.get("selected_company")
        logger.info("selected_company from session: %s", selected_company)

    if not selected_company or selected_company == "all":
        api = models.AzureApi.objects.filter(is_primary=True).first()
        logger.info("Looking up primary AzureApi")
    else:
        api = models.AzureApi.objects.filter(company=selected_company).first()
        logger.info("Looking up AzureApi for company: %s", selected_company)

    if api is None:
        logger.error("No AzureApi found — Outlook mail not configured")
        if request:
            messages.info(request, _("Mail not sent — Outlook not configured"))
        return None, email_data

    logger.info("AzureApi found: %s (email: %s)", api.id, api.outlook_email)
    token = api.token
    logger.info("Token present: %s, Token expired: %s", bool(token), api.is_token_expired() if hasattr(api, 'is_token_expired') else 'N/A')

    if not token or api.is_token_expired():
        logger.info("Attempting token refresh")
        try:
            api = refresh_outlook_token(api)
            token = api.token
            logger.info("Token refresh result — token present: %s", bool(token))
        except Exception as e:
            logger.error("Token refresh failed: %s", e, exc_info=True)
            if request:
                messages.error(request, _("Outlook authentication expired — please re-login"))
            return None, email_data

    if not token:
        logger.error("No token available after refresh")
        if request:
            messages.info(request, _("Mail not sent — Outlook authentication required"))
            return redirect("outlook_login")

    oauth = OAuth2Session(
        api.outlook_client_id,
        token=token,
        auto_refresh_kwargs={
            "client_id": api.outlook_client_id,
            "client_secret": api.outlook_client_secret,
        },
        auto_refresh_url=api.outlook_token_url,
    )

    endpoint = f"{api.outlook_api_endpoint}/me/sendMail"
    logger.info("Sending email via Graph API endpoint: %s", endpoint)
    logger.info("Email data keys: %s", list(email_data.keys()) if email_data else None)
    try:
        response = oauth.post(endpoint, json=email_data)
        logger.info("Graph API response status: %s", response.status_code)
        logger.info("Graph API response body: %s", response.text[:500] if response.text else "(empty)")
        response.raise_for_status()
        messages.success(request, _("Mail sent"))
        logger.info("Email sent successfully via Graph API")
        return response, email_data
    except Exception as e:
        logger.error("Graph API send failed: %s", e, exc_info=True)
        if request:
            messages.error(request, _("Something went wrong"))
            messages.info(request, _("Outlook authentication required/expired"))
        return None, email_data


@login_required
@permission_required("outlook_auth.view_azureapi")
def view_outlook_records(request):
    """
    View server records
    """
    return render(request, "outlook/view_records.html")


@login_required
@permission_required("outlook_auth.view_azureapi")
def outlook_test_email(request):
    """
    Send a test email via the configured Outlook / Microsoft Graph API.
    On GET returns a simple form; on POST sends the test and returns HttpResponse
    so the HTMX toast is displayed.
    """
    from django.template import loader

    email_to = request.POST.get("email_to", "").strip() if request.method == "POST" else ""
    sent = False

    if request.method == "POST" and email_to:
        try:
            company = request.user.employee_get.employee_work_info.company_id
        except Exception:
            company = None

        selected_company = request.session.get("selected_company")
        if not selected_company or selected_company == "all":
            api = models.AzureApi.objects.filter(is_primary=True).first()
        else:
            api = models.AzureApi.objects.filter(company=selected_company).first()

        if api is None:
            messages.error(request, _("No Outlook API configured for your company."))
        else:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            email_data = {
                "message": {
                    "subject": _("Horilla – Outlook test email"),
                    "body": {
                        "contentType": "HTML",
                        "content": f"<h3>{_('Test email')}</h3><p>{_('Sent at')}: {now}</p>",
                    },
                    "toRecipients": [
                        {"emailAddress": {"address": email_to}}
                    ],
                },
            }
            response, _ = send_outlook_email(request, email_data)
            sent = response is not None
            if sent:
                logger.info("Outlook test email sent successfully to %s", email_to)

    html = loader.render_to_string(
        "outlook/test_email_form.html",
        {"email_to": email_to, "sent": sent},
        request,
    )
    return HttpResponse(html)
