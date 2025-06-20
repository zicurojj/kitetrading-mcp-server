# 🚀 Production Deployment Guide - Digital Ocean

## ✅ **Your application is fully containerized and ready for Digital Ocean!**

## 📦 **What's Included**

### **Core Application Files:**
- `fastapi_server.py` - Main FastAPI server
- `docker_auth.py` - Authentication system
- `browser_auth.py` - Browser-assisted auth
- `trade.py` - Trading functions
- `logger.py` - Logging utilities

### **Docker Configuration:**
- `Dockerfile` - Optimized container build
- `docker-compose.yml` - Development deployment
- `docker-compose.prod.yml` - Production deployment
- `deploy.sh` - Automated deployment script

### **Utilities:**
- `client_example.py` - API testing client
- `openapi_schema.py` - ChatGPT schema generator
- `CHATGPT_INTEGRATION.md` - Integration guide

## 🌊 **Digital Ocean Deployment**

### **Step 1: Prepare Your Droplet**

```bash
# SSH into your Digital Ocean droplet
ssh root@your-droplet-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### **Step 2: Deploy Your Application**

```bash
# Clone/upload your code to the droplet
# Option A: Git clone
git clone your-repo-url
cd kite-mcp-server2

# Option B: SCP upload
scp -r . root@your-droplet-ip:/app/kite-trading/
ssh root@your-droplet-ip
cd /app/kite-trading/

# Create environment file
cp .env.example .env
nano .env  # Edit with your actual Kite Connect credentials

# Make deploy script executable
chmod +x deploy.sh

# Deploy (development)
./deploy.sh dev

# OR Deploy (production)
./deploy.sh prod
```

### **Step 3: Configure Environment**

Edit your `.env` file:
```env
# Kite Connect API Credentials
KITE_API_KEY=your_actual_api_key
KITE_API_SECRET=your_actual_api_secret
KITE_REDIRECT_URI=http://your-droplet-ip:8080/callback

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
DEBUG=false

# Directories
DATA_DIR=./data
LOG_DIR=./logs

# Browser-Assisted Re-authentication
BROWSER_REAUTH=true
```

### **Step 4: Initial Authentication**

```bash
# Run browser-assisted authentication
docker-compose exec kite-trading python browser_auth.py

# This will:
# 1. Show you a URL to open in your browser
# 2. You complete login + OTP
# 3. System captures token automatically
# 4. Session is saved for future use
```

## 🔧 **Production Configuration**

### **Environment Variables**
```bash
# Production environment
ENVIRONMENT=production
DOCKER_MODE=true
BROWSER_REAUTH=true

# Security
DEBUG=false
LOG_LEVEL=INFO

# Performance
WORKERS=4
MAX_CONNECTIONS=1000
```

### **Resource Limits**
```yaml
# In docker-compose.prod.yml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

## 🌐 **Accessing Your API**

### **Development (port 8080)**
- API: `http://your-droplet-ip:8080/`
- Docs: `http://your-droplet-ip:8080/docs`
- Health: `http://your-droplet-ip:8080/`

### **Production (port 80)**
- API: `http://your-droplet-ip/`
- Docs: `http://your-droplet-ip/docs`
- Health: `http://your-droplet-ip/`

## 🤖 **ChatGPT Integration**

### **Generate Schema**
```bash
# Generate OpenAPI schema for ChatGPT
docker-compose exec kite-trading python openapi_schema.py

# Download the schema
docker cp kite-trading-server:/app/chatgpt_schema.json ./
```

### **Configure ChatGPT Custom GPT**
1. **Base URL**: `http://your-droplet-ip:8080`
2. **Schema**: Upload `chatgpt_schema.json`
3. **Authentication**: None (handled by server)

## 📊 **Monitoring & Maintenance**

### **Check Status**
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs -f kite-trading

# Check health
curl http://your-droplet-ip:8080/

# Check authentication
curl http://your-droplet-ip:8080/auth/status
```

### **Restart Services**
```bash
# Restart application
docker-compose restart kite-trading

# Full redeploy
./deploy.sh prod
```

### **Backup Data**
```bash
# Backup volumes
docker run --rm -v kite_data:/data -v $(pwd):/backup alpine tar czf /backup/kite-data-backup.tar.gz -C /data .
docker run --rm -v kite_logs:/logs -v $(pwd):/backup alpine tar czf /backup/kite-logs-backup.tar.gz -C /logs .
```

## 🔒 **Security Considerations**

### **Firewall Configuration**
```bash
# Configure UFW firewall
ufw allow ssh
ufw allow 8080/tcp  # Development
ufw allow 80/tcp    # Production
ufw allow 443/tcp   # HTTPS (future)
ufw enable
```

### **SSL/HTTPS (Recommended)**
```bash
# Install Certbot for Let's Encrypt
apt install certbot

# Get SSL certificate
certbot certonly --standalone -d your-domain.com

# Update nginx configuration for HTTPS
```

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Port conflicts**
   ```bash
   # Check what's using port 8080
   netstat -tulpn | grep 8080
   
   # Kill conflicting process
   sudo kill -9 PID
   ```

2. **Authentication failures**
   ```bash
   # Re-authenticate
   docker-compose exec kite-trading python browser_auth.py
   
   # Check logs
   docker-compose logs kite-trading | grep -i auth
   ```

3. **Container won't start**
   ```bash
   # Check logs
   docker-compose logs kite-trading
   
   # Rebuild container
   docker-compose build --no-cache
   ```

## ✅ **Deployment Checklist**

- [ ] Digital Ocean droplet created
- [ ] Docker and Docker Compose installed
- [ ] Code uploaded to droplet
- [ ] `.env` file configured with real credentials
- [ ] Deployment script executed successfully
- [ ] Initial authentication completed
- [ ] API endpoints responding
- [ ] ChatGPT schema generated
- [ ] Firewall configured
- [ ] Monitoring set up

## 🎯 **Final Result**

Your Kite Trading Server is now:
- ✅ **Fully containerized** with Docker
- ✅ **Production ready** on Digital Ocean
- ✅ **ChatGPT compatible** with proper API schema
- ✅ **Secure** with proper authentication
- ✅ **Scalable** with Docker Compose
- ✅ **Monitored** with health checks and logging

**You can now trade using ChatGPT with natural language commands!** 🚀
