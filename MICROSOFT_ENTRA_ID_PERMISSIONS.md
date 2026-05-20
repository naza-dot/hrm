# Microsoft Entra ID App Registration Permissions

This document outlines the permissions required for the Horilla HRM Microsoft SSO app registration to function properly, including user authentication and user synchronization from Microsoft Entra ID.

## Overview

The Horilla HRM system uses Microsoft Entra ID (Azure AD) for:
1. **User Authentication (SSO)** - Users can sign in with their Microsoft account
2. **User Synchronization** - Admins can sync all users from the organization to HRM

## Required App Registration Permissions

### 1. For User Authentication (SSO Login)

These permissions are required for the "Sign in with Microsoft" functionality:

#### Delegated Permissions (user-context)
- **OpenID Connect scopes:**
  - `openid` - Sign in user and read user profile
  - `profile` - Read user profile
  - `email` - Read user email address

**Purpose:** These allow users to sign in and for the application to access their basic profile information and email address.

### 2. For User Synchronization

These permissions are required for the "Sync Users from Entra ID" feature:

#### Application Permissions (app-context, no user needed)
- **Microsoft Graph API:**
  - `User.Read.All` - Read all user profiles in the directory
  - `User.ReadWrite.All` (optional) - If you plan to modify user data in Entra ID from HRM

**Purpose:** These allow the application to use the Client Credentials flow to fetch all users in the organization without requiring user interaction.

## Step-by-Step Setup in Azure Portal

### Prerequisites
- Admin access to Azure Portal
- Access to create app registrations in your tenant

### Steps

#### 1. Create/Update App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Entra ID** → **App registrations**
3. Click **New registration** (or select existing app)
4. Fill in the details:
   - **Name:** Horilla HRM (or your preferred name)
   - **Supported account types:** Select based on your needs:
     - "Accounts in this organizational directory only" (Single tenant)
     - "Multitenant" (if needed)
   - **Redirect URI:** Select **Web** and enter:
     - `https://your-domain.com/login-microsoft/callback/`
     - For development: `http://localhost:8000/login-microsoft/callback/`

5. Click **Register**

#### 2. Configure API Permissions

1. In the app registration, go to **API permissions**
2. Click **Add a permission**

**For User Authentication:**
1. Select **Microsoft Graph**
2. Select **Delegated permissions**
3. Search for and select:
   - `openid`
   - `profile`
   - `email`
4. Click **Add permissions**

**For User Synchronization:**
1. Click **Add a permission** again
2. Select **Microsoft Graph**
3. Select **Application permissions**
4. Search for and select:
   - `User.Read.All` - Required for syncing users
   - `User.ReadWrite.All` - Optional, only if modifying users in Entra ID
5. Click **Add permissions**

#### 3. Grant Admin Consent

1. After adding permissions, click **Grant admin consent for [Organization Name]**
2. Confirm the action
3. Wait a few moments for the changes to propagate

#### 4. Create Client Credentials

1. Go to **Certificates & secrets**
2. Under **Client secrets**, click **New client secret**
3. Add a description: "Horilla HRM Sync"
4. Choose an expiration:
   - **6 months, 12 months, 18 months, or 24 months**
   - Or **Never** (not recommended for security)
5. Click **Add**
6. **Copy the value immediately** (you won't be able to see it again)
   - This is your **Client Secret**

#### 5. Copy Required Values

You'll need these values to configure Horilla HRM:

1. **Client ID** (Application ID):
   - Found on the **Overview** page
   - Copy the "Application (client) ID" value

2. **Tenant ID**:
   - Found on the **Overview** page
   - Copy the "Directory (tenant) ID" value

3. **Client Secret**:
   - From the **Certificates & secrets** page
   - Already copied in step 4

### 6. Configure Horilla HRM

1. Log in to Horilla HRM as an admin
2. Go to **Settings** → **Microsoft SSO**
3. Fill in the values:
   - **Client ID:** Paste the Application (client) ID
   - **Client Secret:** Paste the Client Secret value
   - **Tenant ID:** Paste the Directory (tenant) ID
4. Click **Save Settings**
5. Verify the **Redirect URI** shown matches what you configured in Azure

## Permission Details

### User.Read.All

- **Type:** Application Permission
- **Risk Level:** High
- **Purpose:** Allows the application to read all user profiles in the directory
- **What it provides:** Access to user information including:
  - Display Name
  - Email addresses
  - Phone numbers
  - Job titles
  - Office locations
  - User IDs
- **When used:** During the "Sync Users from Entra ID" operation
- **Requires admin consent:** Yes

### User.ReadWrite.All

- **Type:** Application Permission
- **Risk Level:** Critical
- **Purpose:** Allows modifying user information in Entra ID
- **When needed:** Only if you plan to update user attributes in Entra ID from HRM
- **Default requirement:** Optional for current implementation
- **Requires admin consent:** Yes

## Testing the Setup

### Test User Authentication
1. Navigate to the login page
2. Click **"Sign in with Microsoft"**
3. Sign in with your Microsoft account
4. You should be redirected back to HRM and logged in

### Test User Synchronization
1. Go to **Settings** → **Microsoft SSO** (must be admin)
2. Click **"Sync Users from Entra ID"**
3. Wait for the sync to complete
4. Check the **Users** section to see synchronized users

## Troubleshooting

### "Invalid redirect URI" error
- Ensure the redirect URI in Azure exactly matches the one shown in Horilla settings
- Check for trailing slashes and HTTP vs HTTPS

### "Insufficient privileges" error
- Ensure permissions have been granted admin consent
- Check that `User.Read.All` is added as an **Application Permission** (not delegated)

### "Invalid Client" error
- Verify the Client ID and Client Secret are correct
- Check that the Client Secret hasn't expired
- If expired, create a new client secret

### Users not syncing
- Ensure the Tenant ID is correct
- Verify that the app has `User.Read.All` permission
- Check browser console for detailed error messages
- Ensure the user clicking "Sync Users" is a superuser/admin

### "AADSTS900561: The resource does not exist in the directory" error
- Verify the Tenant ID is correct
- This usually means the tenant ID doesn't match your Entra ID tenant

## Security Best Practices

1. **Rotate Client Secrets Regularly**
   - Set an expiration date (e.g., 12 months)
   - Create new secrets before old ones expire
   - Delete old secrets immediately after rotation

2. **Monitor Permission Usage**
   - Regularly review which users/apps have access
   - Remove unused app registrations

3. **Use Conditional Access**
   - Implement Conditional Access policies in Azure
   - Require MFA for sensitive operations
   - Restrict access by device compliance

4. **Audit Logs**
   - Monitor audit logs for unauthorized access attempts
   - Set up alerts for critical changes

5. **Environment-Specific Credentials**
   - Use different app registrations for dev, staging, and production
   - Never share credentials between environments

## Additional Resources

- [Microsoft Graph API Documentation](https://docs.microsoft.com/en-us/graph/overview)
- [Azure AD Application Permissions](https://docs.microsoft.com/en-us/graph/permissions-reference)
- [OAuth 2.0 and OpenID Connect in Azure AD](https://docs.microsoft.com/en-us/azure/active-directory/develop/active-directory-v2-protocols)
- [User Resource in Microsoft Graph](https://docs.microsoft.com/en-us/graph/api/resources/user)

## Support

For issues or questions about Microsoft Entra ID integration, please:
1. Check the troubleshooting section above
2. Review the Horilla HRM documentation
3. Check Azure AD audit logs for error messages
4. Contact your Microsoft support or Horilla support team
