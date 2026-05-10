# Microsoft OAuth Authentication Setup

This guide explains how to configure Microsoft OAuth authentication for Horilla HRM.

## Prerequisites

- Microsoft Azure account with appropriate permissions
- Access to Azure Portal

## Step 1: Register Application in Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Fill in the application details:
   - **Name**: Horilla HRM (or your preferred name)
   - **Supported account types**: Choose one of:
     - "Accounts in any organizational directory (Any Azure AD directory - Multitenant)" for multi-tenant
     - "Accounts in this organizational directory only" for single-tenant
   - **Redirect URI**: Select **Web** and enter `http://localhost:8000/login-microsoft/callback/` (for development)
5. Click **Register**

## Step 2: Configure Application

1. After registration, note down:
   - **Application (client) ID**
   - **Directory (tenant) ID**

2. Go to **Certificates & secrets**
3. Click **New client secret**
4. Add a description and choose an expiration period
5. Click **Add**
6. **Important**: Copy the client secret immediately as it won't be shown again

3. Go to **Authentication**
4. Under **Implicit grant and hybrid flows**, check:
   - **ID tokens (used for implicit and hybrid flows)**
   - **Access tokens (used for implicit flows)**
5. Click **Save**

## Step 3: Configure Environment Variables

Add the following to your `.env` file:

```env
MICROSOFT_AUTH_CLIENT_ID=your-application-client-id
MICROSOFT_AUTH_CLIENT_SECRET=your-client-secret
MICROSOFT_AUTH_TENANT_ID=common  # or your specific tenant ID
```

Replace the values with:
- `your-application-client-id`: The Application (client) ID from Azure
- `your-client-secret`: The client secret you created
- `common`: Use `common` for multi-tenant apps, or your specific tenant ID for single-tenant

## Step 4: Update Redirect URI (Production)

For production deployment, update the redirect URI:

1. In Azure Portal, go to your app registration
2. Navigate to **Authentication**
3. Under **Redirect URIs**, update the URI to your production URL:
   - `https://your-domain.com/login-microsoft/callback/`
4. Click **Save**

## Step 5: Test the Configuration

1. Restart your Django application
2. Navigate to the login page
3. Click "Sign in with Microsoft"
4. You should be redirected to Microsoft's login page
5. After successful authentication, you'll be redirected back to your application

## How It Works

1. **User clicks "Sign in with Microsoft"** → Redirects to Microsoft OAuth
2. **User authenticates with Microsoft** → Receives authorization code
3. **Application exchanges code for access token** → Gets user profile information
4. **User account is created/updated** → User is logged into Horilla HRM

## Security Notes

- Always use HTTPS in production
- Store client secrets securely
- Regularly rotate client secrets
- Monitor application usage in Azure Portal

## Troubleshooting

### Common Issues

1. **"Invalid authentication state" error**
   - Ensure cookies are enabled in your browser
   - Clear browser cache and try again

2. **"Authentication failed" error**
   - Check that your client ID and secret are correct
   - Verify the redirect URI matches exactly

3. **"Could not retrieve email" error**
   - Ensure the Microsoft account has an email address
   - Check that the correct permissions are granted

4. **Redirect loop**
   - Check that your redirect URI is correctly configured in Azure
   - Ensure CORS is properly configured for your domain

### Debug Mode

Add the following to your Django settings for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will provide detailed logs of the OAuth flow.

## Support

If you encounter issues:

1. Check the Azure Portal application logs
2. Review Django error logs
3. Verify all configuration values
4. Ensure your application has the necessary permissions in Azure

## Additional Features

The Microsoft OAuth integration includes:

- **Automatic user creation**: New Microsoft users are automatically created in Horilla
- **Profile synchronization**: User profile information is synchronized from Microsoft
- **Secure authentication**: Uses OAuth 2.0 with proper state validation
- **Error handling**: Comprehensive error messages for troubleshooting
