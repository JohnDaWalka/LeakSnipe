# GETTING STARTED WITH REX POKER COACH

## Quick Setup Steps

### 1. Initial Setup
```bash
# Clone or navigate to repo
cd rex-poker-coach

# Install dependencies
npm install

# Copy environment file
copy config\.env.example .env
# Edit .env with your configuration
```

### 2. Start Services
```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Services will be available at:
# - API: http://localhost:3001
# - ChromaDB: http://localhost:8000
# - PostgreSQL: localhost:5432
```

### 3. Verify Installation
```bash
# Check API health
curl http://localhost:3001/health

# Expected response:
# {"status":"ok","initialized":false,"timestamp":"2024-01-17T..."}
```

### 4. Initialize System
```bash
# Sync hands from PT4
curl -X POST http://localhost:3001/api/sync-hands \
  -H "Content-Type: application/json" \
  -d "{\"limit\": 100}"
```

### 5. Test Analysis
```bash
# Analyze a hand
curl -X POST http://localhost:3001/api/analyze-hand \
  -H "Content-Type: application/json" \
  -d "{\"handId\": 12345}"
```

## Azure Deployment

### Prerequisites
- Azure CLI installed
- Azure subscription
- Docker registry (ACR)

### Deploy to Azure
```bash
# 1. Create resource group
az group create -n rex-poker-coach-rg -l eastus

# 2. Create Container Registry
az acr create -g rex-poker-coach-rg -n rexregistryname --sku Basic

# 3. Build and push image
docker build -t rex-poker-coach:latest .
docker tag rex-poker-coach:latest rexregistryname.azurecr.io/rex-poker-coach:latest

az acr login -n rexregistryname
docker push rexregistryname.azurecr.io/rex-poker-coach:latest

# 4. Deploy infrastructure
az deployment group create \
  --resource-group rex-poker-coach-rg \
  --template-file azure/main.bicep \
  --parameters azure/parameters.json

# 5. Get deployed URL
az deployment group show -g rex-poker-coach-rg -n main --query properties.outputs
```

## Troubleshooting

### ChromaDB Connection Issues
```bash
# Check if ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# Restart ChromaDB
docker-compose restart chromadb
```

### PostgreSQL Connection Issues
```bash
# Check connection
psql -h localhost -U postgres -d PT4DB

# View logs
docker-compose logs postgres
```

### API Not Responding
```bash
# Check container logs
docker-compose logs rex-api

# Restart API
docker-compose restart rex-api
```

## Next Steps

1. **Configure PT4 Connection**: Update `.env` with your PT4 database credentials
2. **Sync Hand History**: Import your poker hands into the system
3. **Run Analysis**: Start analyzing hands and sessions
4. **Monitor Performance**: Use Azure Application Insights for monitoring
5. **Customize Rules**: Adjust tilt detection thresholds in config

For detailed documentation, see [README.md](../README.md)
