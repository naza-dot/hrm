# Entra ID Property Mapping Documentation

This document describes how Microsoft Entra ID (Azure AD) user properties are fetched and mapped to Horilla HRM fields during user synchronization.

## Overview

When syncing users from Microsoft Entra ID, the system fetches user information from the Microsoft Graph API and maps it to corresponding fields in the Horilla HRM database. This ensures that employee information is automatically populated and kept synchronized with your Entra ID tenant.

## Property Mappings

### User Profile Information

| Entra ID Property | HRM Field | Model | Notes |
|---|---|---|---|
| `displayName` | Employee full name | Employee | Split into `employee_first_name` and `employee_last_name` |
| `givenName` | `employee_first_name` | Employee | First name from Entra ID |
| `surname` | `employee_last_name` | Employee | Last name from Entra ID |
| `mail` | `email` | Employee | Primary email address |
| `userPrincipalName` | Fallback `email` | Employee | Used if `mail` is not available |

### Work Information

| Entra ID Property | HRM Field | Model | Notes |
|---|---|---|---|
| `jobTitle` | Job Position | EmployeeWorkInformation | Creates new Job Position if it doesn't exist |
| `department` | Department | EmployeeWorkInformation | Creates new Department if it doesn't exist |
| `companyName` | Company | EmployeeWorkInformation | Creates new Company if it doesn't exist; uses HQ company as fallback |
| `officeLocation` | Work Location (`location`) | EmployeeWorkInformation | Physical office/work location |
| `employeeId` | Badge ID (`badge_id`) | Employee | Unique employee identifier from Entra ID |
| `employeeType` | Employee Type (`employee_type_id`) | EmployeeWorkInformation | Examples: FTE, Contractor, Part-time, etc. |
| `employeeHireDate` | Joining Date (`date_joining`) | EmployeeWorkInformation | Employee hire date (ISO format: YYYY-MM-DD) |

### Contact Information

| Entra ID Property | HRM Field | Model | Notes |
|---|---|---|---|
| `mobilePhone` | Phone | Employee | Personal mobile phone |
| `businessPhones[0]` | Work Phone (`mobile`) | EmployeeWorkInformation | Work phone (first number in array) |

### Manager Information

| Entra ID Property | HRM Field | Model | Notes |
|---|---|---|---|
| `manager` (via `/manager` endpoint) | Reporting Manager (`reporting_manager_id`) | EmployeeWorkInformation | Resolved in second sync pass |

## Detailed Field Descriptions

### Job Position
- **Source:** `jobTitle` from Entra ID
- **Destination:** `EmployeeWorkInformation.job_position_id` (ForeignKey to JobPosition)
- **Behavior:** If the job title doesn't exist as a Job Position in HRM, it's automatically created
- **Company:** Job Position is created under the same company as the employee

### Company
- **Source:** `companyName` from Entra ID
- **Destination:** `EmployeeWorkInformation.company_id` (ForeignKey to Company)
- **Behavior:** If the company doesn't exist, it's automatically created
- **Fallback:** Uses HQ company (marked as headquarters) if no company name is provided
- **Company Creation:** New companies are created with minimal information; you may need to edit them to add address, location, etc.

### Department
- **Source:** `department` from Entra ID
- **Destination:** `EmployeeWorkInformation.department_id` (ForeignKey to Department)
- **Behavior:** If the department doesn't exist, it's automatically created
- **Company:** Department is associated with the employee's company

### Employee ID
- **Source:** `employeeId` from Entra ID
- **Destination:** `Employee.badge_id`
- **Behavior:** Unique identifier for the employee
- **Constraints:** Must be unique (when not null)
- **Max Length:** 50 characters

### Employee Type
- **Source:** `employeeType` from Entra ID
- **Destination:** `EmployeeWorkInformation.employee_type_id` (ForeignKey to EmployeeType)
- **Behavior:** If the employee type doesn't exist, it's automatically created
- **Common Values:** FTE, Contractor, Part-time, Intern, Temporary, etc.
- **Company Association:** Employee Type is associated with the employee's company

### Joining Date (Employee Hire Date)
- **Source:** `employeeHireDate` from Entra ID
- **Destination:** `EmployeeWorkInformation.date_joining`
- **Format:** ISO 8601 date format (YYYY-MM-DD)
- **Behavior:** Automatically parsed from Entra ID format
- **Error Handling:** If the date cannot be parsed, the field is left empty
- **Calculation:** Used to calculate employee experience

### Work Location
- **Source:** `officeLocation` from Entra ID
- **Destination:** `EmployeeWorkInformation.location`
- **Max Length:** 50 characters
- **Notes:** Can store office name, city, or location code

### Work Phone
- **Source:** `businessPhones[0]` from Entra ID
- **Destination:** `EmployeeWorkInformation.mobile`
- **Behavior:** Takes the first phone number from the array
- **Max Length:** 254 characters

### Reporting Manager
- **Source:** Manager resolved via Microsoft Graph `/users/{userId}/manager` endpoint
- **Destination:** `EmployeeWorkInformation.reporting_manager_id` (ForeignKey to Employee)
- **Behavior:** 
  - Resolved in a second pass after all employees are synced
  - Only set if both the employee and their manager are found in the system
  - Silently skipped if manager is not found or user has no manager assigned
- **Note:** Requires `User.Read.All` permission with ability to read manager relationships

## Sync Process

The synchronization process follows these steps:

1. **Authentication:** Acquires access token using client credentials (application permissions)
2. **User Fetching:** Retrieves all users from the tenant using Microsoft Graph API
3. **User Sync (First Pass):**
   - Creates or updates User and Employee records
   - Maps all basic profile information
   - Creates Job Position, Department, Company, and Employee Type records as needed
4. **Manager Mapping (Second Pass):**
   - Fetches manager information for each user
   - Links employees to their reporting managers

## Error Handling

- **Missing Required Fields:** Employees are created with minimal information if some fields are missing
- **Invalid Dates:** If `employeeHireDate` cannot be parsed, the field is left empty
- **Missing Manager:** If a manager is not found in the system, the field is left empty
- **Duplicate Entries:** Existing employees are updated rather than duplicated

## Permissions Required

To enable full user synchronization from Entra ID, your app registration must have the following permissions:

### Delegated Permissions
- `openid` - Sign in user
- `profile` - Read user profile
- `email` - Read user email

### Application Permissions
- `User.Read.All` - Read all user profiles
- (Optional) `User.ReadWrite.All` - If you need to modify user data in Entra ID

See [MICROSOFT_ENTRA_ID_PERMISSIONS.md](./MICROSOFT_ENTRA_ID_PERMISSIONS.md) for detailed setup instructions.

## Troubleshooting

### Properties not syncing
1. Check that the required properties exist in your Entra ID tenant
2. Verify that the app registration has `User.Read.All` permission
3. Ensure the syncing user is a superuser/admin

### Missing manager assignments
1. Verify that all employees in the sync list are present in the database
2. Check that managers have email addresses that match the employee records
3. Review error logs for specific manager mapping failures

### Company/Department not created correctly
- New companies and departments are created with minimal information
- Edit them in the HRM admin panel to add complete information
- The system will reuse existing companies/departments if the name matches exactly

## API Endpoint

**URL:** `/api/microsoft-sync-users/` or `POST /base/microsoft-sync-users/`
**Method:** POST
**Authentication:** User must be authenticated and be a superuser
**Response:** JSON with sync statistics and any errors encountered

### Response Example
```json
{
    "success": true,
    "synced_count": 150,
    "total_users": 150,
    "message": "Successfully synced 150 users from Microsoft Entra ID",
    "hq_company": "HQ (12345678...)",
    "errors": null
}
```

## Important Notes

1. **Data Synchronization:** The sync is one-way only (Entra ID → HRM). Changes in HRM are not synced back to Entra ID.
2. **First Time Setup:** The first sync may take some time if you have many users. Subsequent syncs are faster as they update existing records.
3. **Regular Syncing:** It's recommended to sync regularly (e.g., weekly) to keep employee information up-to-date.
4. **Manual Edits:** Any manual edits in HRM will be overwritten during the next sync if the corresponding Entra ID property has changed.
5. **Job Position and Department:** These are matched by exact name. If you rename them in HRM, new entries will be created during the next sync.

## Examples

### Example 1: Basic User Sync
An Entra ID user with the following properties:
```
displayName: "John Smith"
givenName: "John"
surname: "Smith"
mail: "john.smith@company.com"
jobTitle: "Senior Developer"
department: "Engineering"
companyName: "Acme Corp"
officeLocation: "New York"
employeeId: "EMP-12345"
employeeType: "FTE"
employeeHireDate: "2020-01-15"
manager: "jane.doe@company.com"
mobilePhone: "+1-555-0123"
businessPhones: ["+1-555-9876"]
```

Will be synced to HRM as:
- **Employee:** John Smith (john.smith@company.com)
- **Badge ID:** EMP-12345
- **Job Position:** Senior Developer
- **Department:** Engineering
- **Company:** Acme Corp
- **Work Location:** New York
- **Employee Type:** FTE
- **Joining Date:** 2020-01-15
- **Reporting Manager:** Jane Doe (if found)

### Example 2: Partial Data
If some fields are missing:
```
displayName: "Jane Doe"
mail: "jane.doe@company.com"
```

An employee will still be created with basic information, and the missing fields will be left empty. They can be filled in manually later.

## Related Documentation

- [Microsoft Entra ID Permissions Setup](./MICROSOFT_ENTRA_ID_PERMISSIONS.md)
- [Microsoft SSO Setup](./MICROSOFT_AUTH_SETUP.md)
- [Microsoft SSO Changes](./MICROSOFT_SSO_CHANGES.md)
