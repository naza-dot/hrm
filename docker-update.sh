#!/bin/bash

##############################################################################
# HRM Docker Update Script
# This script automates the process of updating Horilla HRM on Docker
# 
# Usage: ./docker-update.sh [option]
# Options:
#   full      - Full update with rebuild (recommended)
#   quick     - Quick update with existing image
#   minimal   - Update without stopping containers
#   migrate   - Only run database migrations
#   logs      - View container logs
#   status    - Show container status
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BRANCH="dev-sso-2"
COMPOSE_FILE="docker-compose.yaml"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to print header
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Function: Show status
show_status() {
    print_header "Container Status"
    docker-compose ps
}

# Function: View logs
view_logs() {
    print_header "Container Logs (Press Ctrl+C to exit)"
    docker-compose logs -f
}

# Function: Minimal update
minimal_update() {
    print_header "Minimal Update (Pull + Restart Container)"
    
    print_info "Pulling latest changes from $BRANCH..."
    git pull origin $BRANCH
    
    print_info "Restarting web server container..."
    docker-compose restart server
    
    print_info "Running database migrations..."
    docker-compose exec server python manage.py migrate
    
    print_success "Minimal update completed!"
}

# Function: Quick update
quick_update() {
    print_header "Quick Update (No Cache Rebuild)"
    
    print_info "Pulling latest changes from $BRANCH..."
    git pull origin $BRANCH
    
    print_info "Stopping services..."
    docker-compose down
    
    print_info "Starting services..."
    docker-compose up -d
    
    print_info "Running database migrations..."
    docker-compose exec server python manage.py migrate
    
    print_info "Collecting static files..."
    docker-compose exec server python manage.py collectstatic --noinput
    
    print_success "Quick update completed!"
}

# Function: Full update
full_update() {
    print_header "Full Update (Recommended)"
    
    print_info "Pulling latest changes from $BRANCH..."
    git pull origin $BRANCH
    
    print_info "Stopping services..."
    docker-compose down
    
    print_info "Building Docker image (no cache)..."
    docker-compose build --no-cache
    
    print_info "Starting services..."
    docker-compose up -d
    
    print_info "Running database migrations..."
    docker-compose exec server python manage.py migrate
    
    print_info "Collecting static files..."
    docker-compose exec server python manage.py collectstatic --noinput
    
    print_info "Creating cache table..."
    docker-compose exec server python manage.py createcachetable 2>/dev/null || true
    
    print_success "Full update completed!"
}

# Function: Run migrations only
run_migrations() {
    print_header "Running Database Migrations"
    
    print_info "Running migrations..."
    docker-compose exec server python manage.py migrate
    
    print_success "Migrations completed!"
}

# Function: Show help
show_help() {
    cat << EOF
${BLUE}HRM Docker Update Script${NC}

${YELLOW}Usage:${NC}
  ./docker-update.sh [option]

${YELLOW}Options:${NC}
  full      - Full update with rebuild (recommended for production)
  quick     - Quick update with existing image (faster)
  minimal   - Update without stopping containers (for minor changes)
  migrate   - Only run database migrations
  logs      - View container logs
  status    - Show container status
  help      - Show this help message

${YELLOW}Examples:${NC}
  ./docker-update.sh full      # Full rebuild and start
  ./docker-update.sh quick     # Quick restart with new code
  ./docker-update.sh logs      # View live logs
  ./docker-update.sh status    # Check service status

${YELLOW}Notes:${NC}
  - Ensure you are in the HRM project directory
  - Docker and Docker Compose must be installed
  - Backup your database before running full update
  - Configure .env with Microsoft credentials if using SSO

EOF
}

# Main script logic
main() {
    # Check if docker-compose.yaml exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "docker-compose.yaml not found!"
        print_error "Please run this script from the HRM project root directory"
        exit 1
    fi
    
    # Parse command line argument
    COMMAND=${1:-help}
    
    case "$COMMAND" in
        full)
            full_update
            ;;
        quick)
            quick_update
            ;;
        minimal)
            minimal_update
            ;;
        migrate)
            run_migrations
            ;;
        logs)
            view_logs
            ;;
        status)
            show_status
            ;;
        help)
            show_help
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
