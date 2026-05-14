"""
Microsoft SSO Settings and Graph API Integration Module

This module handles reading Microsoft SSO configuration and provides
functionality to interact with Microsoft Graph API for user synchronization.
"""

import requests
from django.conf import settings
from django.core.cache import cache
from typing import Dict, List, Optional, Tuple


class MicrosoftSSOSettings:
    """
    Class to read and manage Microsoft SSO settings from Django configuration.
    """
    
    def __init__(self):
        """
        Initialize Microsoft SSO settings from Django settings.
        """
        self.client_id = getattr(settings, 'MICROSOFT_AUTH_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'MICROSOFT_AUTH_CLIENT_SECRET', '')
        self.tenant_id = getattr(settings, 'MICROSOFT_AUTH_TENANT_ID', 'common')
        self.graph_api_endpoint = 'https://graph.microsoft.com/v1.0'
        self.auth_endpoint = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0'
    
    def is_configured(self) -> bool:
        """
        Check if Microsoft SSO is properly configured.
        
        Returns:
            bool: True if all required settings are configured, False otherwise.
        """
        return bool(self.client_id and self.client_secret and self.tenant_id)
    
    def get_access_token(self) -> Optional[str]:
        """
        Retrieve an access token for Microsoft Graph API using client credentials flow.
        
        Returns:
            Optional[str]: Access token if successful, None otherwise.
        """
        # Check if token is cached
        cache_key = 'microsoft_graph_access_token'
        cached_token = cache.get(cache_key)
        if cached_token:
            return cached_token
        
        if not self.is_configured():
            return None
        
        try:
            token_url = f'{self.auth_endpoint}/token'
            payload = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(token_url, data=payload, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)
            
            # Cache token with expiration time minus 60 seconds buffer
            cache.set(cache_key, access_token, expires_in - 60)
            
            return access_token
            
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving access token: {str(e)}")
            return None
    
    def get_graph_api_headers(self) -> Optional[Dict[str, str]]:
        """
        Generate headers for Microsoft Graph API requests.
        
        Returns:
            Optional[Dict]: Headers dict with Authorization bearer token, or None if token retrieval fails.
        """
        access_token = self.get_access_token()
        if not access_token:
            return None
        
        return {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }


class MicrosoftGraphAPI:
    """
    Class to handle Microsoft Graph API operations for user management.
    """
    
    def __init__(self):
        """
        Initialize Microsoft Graph API handler.
        """
        self.settings = MicrosoftSSOSettings()
        self.endpoint = self.settings.graph_api_endpoint
    
    def fetch_users(self, filters: Optional[str] = None, 
                   properties: Optional[List[str]] = None,
                   page_size: int = 20) -> Optional[List[Dict]]:
        """
        Fetch users from Entra ID (Azure AD).
        
        Args:
            filters (Optional[str]): OData filter query (e.g., "accountEnabled eq true")
            properties (Optional[List[str]]): Specific properties to retrieve
            page_size (int): Number of results per page (max 999)
        
        Returns:
            Optional[List[Dict]]: List of user objects if successful, None otherwise.
        """
        headers = self.settings.get_graph_api_headers()
        if not headers:
            return None
        
        try:
            url = f'{self.endpoint}/users'
            params = {
                '$top': min(page_size, 999)
            }
            
            # Set default properties if not specified
            if not properties:
                properties = [
                    'id',
                    'userPrincipalName',
                    'displayName',
                    'mail',
                    'givenName',
                    'surname',
                    'jobTitle',
                    'department',
                    'officeLocation',
                    'mobilePhone',
                    'accountEnabled'
                ]
            
            params['$select'] = ','.join(properties)
            
            # Add filter if provided
            if filters:
                params['$filter'] = filters
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            users = data.get('value', [])
            
            # Handle pagination
            while '@odata.nextLink' in data:
                response = requests.get(data['@odata.nextLink'], headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                users.extend(data.get('value', []))
            
            return users
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching users from Microsoft Graph: {str(e)}")
            return None
    
    def fetch_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        Fetch a specific user by ID from Entra ID.
        
        Args:
            user_id (str): The user's ID or userPrincipalName
        
        Returns:
            Optional[Dict]: User object if successful, None otherwise.
        """
        headers = self.settings.get_graph_api_headers()
        if not headers:
            return None
        
        try:
            url = f'{self.endpoint}/users/{user_id}'
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user {user_id}: {str(e)}")
            return None
    
    def fetch_users_by_filter(self, filters: str) -> Optional[List[Dict]]:
        """
        Fetch users filtered by OData query.
        
        Args:
            filters (str): OData filter query
        
        Returns:
            Optional[List[Dict]]: List of filtered users if successful, None otherwise.
        """
        return self.fetch_users(filters=filters)
    
    def fetch_active_users(self) -> Optional[List[Dict]]:
        """
        Fetch only active users from Entra ID.
        
        Returns:
            Optional[List[Dict]]: List of active user objects if successful, None otherwise.
        """
        return self.fetch_users(filters='accountEnabled eq true')
    
    def fetch_users_by_department(self, department: str) -> Optional[List[Dict]]:
        """
        Fetch users filtered by department.
        
        Args:
            department (str): Department name to filter by
        
        Returns:
            Optional[List[Dict]]: List of users in the department if successful, None otherwise.
        """
        filter_query = f"department eq '{department}'"
        return self.fetch_users(filters=filter_query)
    
    def fetch_user_group_memberships(self, user_id: str) -> Optional[List[Dict]]:
        """
        Fetch group memberships for a specific user.
        
        Args:
            user_id (str): The user's ID or userPrincipalName
        
        Returns:
            Optional[List[Dict]]: List of group objects if successful, None otherwise.
        """
        headers = self.settings.get_graph_api_headers()
        if not headers:
            return None
        
        try:
            url = f'{self.endpoint}/users/{user_id}/memberOf'
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.json().get('value', [])
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching group memberships for user {user_id}: {str(e)}")
            return None
    
    def get_user_sync_data(self) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Get all user data for synchronization with local database.
        
        Returns:
            Tuple[bool, Optional[List[Dict]], str]: 
                - Success flag
                - List of users if successful
                - Message or error description
        """
        if not self.settings.is_configured():
            return False, None, "Microsoft SSO settings are not configured"
        
        users = self.fetch_active_users()
        if users is None:
            return False, None, "Failed to fetch users from Microsoft Graph API"
        
        return True, users, f"Successfully fetched {len(users)} users from Entra ID"
