# HRM Docker Update Guide

This guide provides commands to update your Horilla HRM instance running on Docker.

## Quick Update Commands

### 1. **Full Update (Recommended)**
Rebuilds the Docker image and restarts services with all updates applied.

```bash
# Pull latest changes
git pull origin dev-sso-2

# Build and start Docker containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

### 2. **Quick Update (Existing Image)**
Updates Python dependencies and applies migrations without rebuilding the entire image.

```bash
# Pull latest changes
git pull origin dev-sso-2

# Update running container with new code
docker-compose down
docker-compose up -d
```

---

### 3. **Minimal Update (Running Container)**
Updates code while keeping the container running (useful for minor changes).

```bash
# Pull latest changes in the background
git pull origin dev-sso-2

# Restart only the web container to apply changes
docker-compose restart server

# Apply any pending database migrations
docker-compose exec server python manage.py migrate
```

---

## Detailed Update Steps

### Step 1: Pull Latest Changes
```bash
cd /path/to/hrm

# Checkout the dev-sso-2 branch
git checkout dev-sso-2

# Pull latest commits
git pull origin dev-sso-2
```

### Step 2: Check Requirements Changes
```bash
# View if requirements.txt changed
git diff HEAD~1 requirements.txt

# If changed, rebuild is necessary
```

### Step 3: Build New Docker Image
```bash
# Build with no cache for fresh dependencies
docker-compose build --no-cache server

# Or just build (uses cache if available)
docker-compose build server
```

### Step 4: Start Services
```bash
# Start all services
docker-compose up -d

# Or start specific service
docker-compose up -d server
```

### Step 5: Run Database Migrations
```bash
# Apply any pending migrations
docker-compose exec server python manage.py migrate

# Create cache table (if using database cache)
docker-compose exec server python manage.py createcachetable
```

---

## Microsoft Entra ID Sync Update

The latest update includes Microsoft Entra ID user synchronization. After updating, configure:

### Environment Variables (.env)
```bash
# Add these to your .env file
MICROSOFT_AUTH_CLIENT_ID= myclient_id
MICROSOFT_AUTH_CLIENT_SECRET= myclient_secret
MICROSOFT_AUTH_TENANT_ID= mytenant_id
### Update docker-compose.yaml
Ensure these environment variables are set in docker-compose.yaml:

```yaml
environment:
  MICROSOFT_AUTH_CLIENT_ID: ${MICROSOFT_AUTH_CLIENT_ID}
  MICROSOFT_AUTH_CLIENT_SECRET: ${MICROSOFT_AUTH_CLIENT_SECRET}
  MICROSOFT_AUTH_TENANT_ID: ${MICROSOFT_AUTH_TENANT_ID}
```

### Access Sync Views
- **Sync Endpoint**: `/sync-microsoft-users/`
- **Preview Endpoint**: `/get-microsoft-users-preview/`
- **Permissions Required**: `auth.add_user`

---

## Common Docker Commands

### View Running Containers
```bash
docker-compose ps
```

### View Container Logs
```bash
# View all services logs
docker-compose logs -f

# View only web server logs
docker-compose logs -f server

# View only database logs
docker-compose logs -f db
```

### Execute Commands in Container
```bash
# Run shell command
docker-compose exec server bash

# Run Django management command
docker-compose exec server python manage.py <command>

# Access database
docker-compose exec db psql -U postgres -d horilla
```

### Stop Services
```bash
# Stop all services (keep volumes)
docker-compose down

# Stop and remove all data (warning: data loss)
docker-compose down -v
```

### Clean Up Docker
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a
```

---

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs server

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Issues
```bash
# Check database status
docker-compose ps db

# Restart database
docker-compose restart db

# Verify connectivity
docker-compose exec server python manage.py dbshell
```

### Static Files Not Loading
```bash
# Collect static files
docker-compose exec server python manage.py collectstatic --noinput

# Restart web server
docker-compose restart server
```

### Microsoft SSO Not Working
```bash
# Verify environment variables in running container
docker-compose exec server python -c "from django.conf import settings; print(settings.MICROSOFT_AUTH_CLIENT_ID)"

# Check if microsoft_sso.py is present
docker-compose exec server ls -la base/microsoft_sso.py

# Test API connectivity
docker-compose exec server python manage.py shell
# In shell:
# from base.microsoft_sso import MicrosoftSSOSettings
# settings = MicrosoftSSOSettings()
# print(settings.is_configured())
```

---

## Deployment Workflow

### Recommended Workflow for Production

1. **Test on Development**
   ```bash
   git checkout dev-sso-2
   git pull origin dev-sso-2
   docker-compose -f docker-compose.dev.yaml up -d
   ```

2. **Verify Changes**
   ```bash
   docker-compose logs -f server
   # Test all functionality
   ```

3. **Deploy to Production**
   ```bash
   git checkout main
   git pull origin dev-sso-2  # Merge dev-sso-2 to main first
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   docker-compose exec server python manage.py migrate
   ```

4. **Verify Production**
   ```bash
   docker-compose ps
   docker-compose logs server
   # Test all functionality
   ```

---

## Update Checklist

- [ ] Pull latest changes: `git pull origin dev-sso-2`
- [ ] Check requirements.txt for new dependencies
- [ ] Set/update Microsoft Entra ID environment variables if needed
- [ ] Rebuild Docker image: `docker-compose build --no-cache`
- [ ] Start services: `docker-compose up -d`
- [ ] Run migrations: `docker-compose exec server python manage.py migrate`
- [ ] Collect static files: `docker-compose exec server python manage.py collectstatic --noinput`
- [ ] Verify logs: `docker-compose logs -f server`
- [ ] Test Microsoft Sync endpoint (if configured)
- [ ] Check all core functionality

---

## Version Information

**Latest Changes (Commit: 3d70c19e)**
- Added Microsoft Entra ID user synchronization system
- MicrosoftSSOSettings class for OAuth configuration
- MicrosoftGraphAPI for Entra ID API integration
- sync_microsoft_users() view for user synchronization
- Employee and EmployeeWorkInformation auto-mapping
- Preview endpoint for non-destructive sync testing

---

## Need Help?

For more information:
- Check [docker.md](docker.md) for additional Docker documentation
- Review [MICROSOFT_AUTH_SETUP.md](MICROSOFT_AUTH_SETUP.md) for SSO configuration
- Check logs: `docker-compose logs -f server`
