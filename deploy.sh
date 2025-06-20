#!/bin/bash

# Kite Trading Server - Digital Ocean Deployment Script
# Usage: ./deploy.sh [environment]
# Environment: dev (default) | prod

set -e

ENVIRONMENT=${1:-dev}
PROJECT_NAME="kite-trading"
COMPOSE_FILE="docker-compose.yml"

echo "🚀 Deploying Kite Trading Server to Digital Ocean"
echo "📦 Environment: $ENVIRONMENT"
echo "=" * 50

# Set compose file based on environment
if [ "$ENVIRONMENT" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    echo "🏭 Using production configuration"
else
    echo "🔧 Using development configuration"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "💡 Please create .env file with your Kite Connect credentials"
    echo "   cp .env.example .env"
    echo "   # Edit .env with your actual credentials"
    exit 1
fi

# Validate required environment variables
echo "🔍 Validating environment variables..."
source .env

required_vars=("KITE_API_KEY" "KITE_API_SECRET" "KITE_REDIRECT_URI")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    printf '   - %s\n' "${missing_vars[@]}"
    echo "💡 Please update your .env file"
    exit 1
fi

echo "✅ Environment variables validated"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down --remove-orphans || true

# Pull latest images and build
echo "🔄 Building application..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Start services
echo "🚀 Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for health check
echo "⏳ Waiting for health check..."
sleep 10

# Check if service is healthy
if docker-compose -f $COMPOSE_FILE ps | grep -q "healthy\|Up"; then
    echo "✅ Deployment successful!"
    
    # Show service information
    echo ""
    echo "📊 Service Status:"
    docker-compose -f $COMPOSE_FILE ps
    
    echo ""
    echo "🌐 Service URLs:"
    if [ "$ENVIRONMENT" = "prod" ]; then
        echo "   API: http://your-droplet-ip/"
        echo "   Docs: http://your-droplet-ip/docs"
    else
        echo "   API: http://your-droplet-ip:8080/"
        echo "   Docs: http://your-droplet-ip:8080/docs"
    fi
    
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Test API: curl http://your-droplet-ip:8080/"
    echo "   2. Authenticate: Run browser_auth.py"
    echo "   3. Configure ChatGPT with your server URL"
    
else
    echo "❌ Deployment failed!"
    echo "📋 Container logs:"
    docker-compose -f $COMPOSE_FILE logs
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
