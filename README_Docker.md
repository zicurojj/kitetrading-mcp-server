# Kite Trading Server - Docker Deployment

🐳 **Containerized trading server for Zerodha Kite Connect API with both MCP and FastAPI support**

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/kite-mcp-server2.git
cd kite-mcp-server2
```

### 2. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Kite Connect credentials
nano .env
```

### 3. Start FastAPI Server
```bash
# Start FastAPI server (default)
docker-compose up fastapi-server

# Or build and run directly
docker build -t kite-trading .
docker run -p 8000:8000 --env-file .env kite-trading
```

### 4. Access API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

## 📋 Available Services

### FastAPI Server (Default)
```bash
# Production deployment
docker-compose up fastapi-server

# With logs
docker-compose up fastapi-server --logs
```

### MCP Server (Claude Desktop)
```bash
# Start MCP server for Claude Desktop integration
docker-compose --profile mcp up mcp-server
```

### Development Server
```bash
# Start with hot reload and source mounting
docker-compose --profile dev up dev-server
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Required: Kite Connect API credentials
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
KITE_REDIRECT_URI=http://localhost:3000/trade/redirect

# Optional: Server configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
LOG_LEVEL=INFO
```

### Docker Compose Profiles
- **Default**: FastAPI server only
- **`mcp`**: MCP server for Claude Desktop
- **`dev`**: Development server with hot reload

## 📦 Docker Commands

### Build Images
```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build fastapi-server

# Build with no cache
docker-compose build --no-cache
```

### Run Services
```bash
# Start FastAPI server (detached)
docker-compose up -d fastapi-server

# Start MCP server
docker-compose --profile mcp up mcp-server

# Start development environment
docker-compose --profile dev up dev-server

# View logs
docker-compose logs -f fastapi-server
```

### Data Persistence
```bash
# Create directories for persistent data
mkdir -p ./data ./logs

# Run with volume mounts
docker-compose up fastapi-server
```

## 🔐 Authentication Setup

### Option 1: Interactive Setup (Recommended)
```bash
# Run authentication setup in container
docker-compose run --rm fastapi-server python setup_auth.py

# Or using entrypoint script
docker-compose run --rm fastapi-server setup-auth
```

### Option 2: Manual Session File
```bash
# If you have existing session file
cp kite_session.json ./data/
docker-compose up fastapi-server
```

## 🌐 API Usage Examples

### Health Check
```bash
curl http://localhost:8000/
```

### Authentication Status
```bash
curl http://localhost:8000/auth/status
```

### Place Buy Order
```bash
curl -X POST http://localhost:8000/trade/buy \
  -H "Content-Type: application/json" \
  -d '{
    "stock": "RELIANCE",
    "qty": 1,
    "exchange": "NSE",
    "product": "CNC",
    "order_type": "MARKET"
  }'
```

### Get Portfolio
```bash
curl http://localhost:8000/trade/positions
```

## 🔍 Monitoring & Debugging

### Container Logs
```bash
# View real-time logs
docker-compose logs -f fastapi-server

# View specific number of lines
docker-compose logs --tail=100 fastapi-server
```

### Container Shell Access
```bash
# Access running container
docker-compose exec fastapi-server bash

# Run one-off commands
docker-compose run --rm fastapi-server python --version
```

### Health Checks
```bash
# Check container health
docker-compose ps

# Manual health check
docker-compose exec fastapi-server curl -f http://localhost:8000/
```

## 🚨 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "8001:8000"  # Use port 8001 instead
   ```

2. **Authentication Failures**
   ```bash
   # Check environment variables
   docker-compose run --rm fastapi-server env | grep KITE
   
   # Re-run authentication setup
   docker-compose run --rm fastapi-server setup-auth
   ```

3. **Permission Issues**
   ```bash
   # Fix data directory permissions
   sudo chown -R $USER:$USER ./data ./logs
   ```

4. **Container Won't Start**
   ```bash
   # Check logs for errors
   docker-compose logs fastapi-server
   
   # Rebuild without cache
   docker-compose build --no-cache fastapi-server
   ```

## 📁 Volume Mounts

- **`./data:/app/data`** - Session files and persistent data
- **`./logs:/app/logs`** - Trading logs and application logs
- **`.:/app`** - Source code (development only)

## 🔒 Security Notes

- Session files are stored in mounted volumes
- API credentials are passed via environment variables
- Container runs as non-root user (`appuser`)
- Sensitive files are excluded via `.dockerignore`

## 🎯 Production Deployment

### Using Docker Swarm
```bash
# Deploy as stack
docker stack deploy -c docker-compose.yml kite-trading
```

### Using Kubernetes
```bash
# Generate Kubernetes manifests
kompose convert -f docker-compose.yml
kubectl apply -f .
```

### Environment-Specific Configs
```bash
# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up

# Staging  
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up
```

---

🎉 **Ready to trade with Docker!** Visit http://localhost:8000/docs for interactive API documentation.
