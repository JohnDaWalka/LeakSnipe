# Azure Deployment Guide for Rex Poker Coach

## Prerequisites Checklist

- [ ] Azure subscription (with sufficient credits/quota)
- [ ] Azure CLI installed (`az --version`)
- [ ] Docker installed (`docker --version`)
- [ ] Git and GitHub account configured
- [ ] PowerShell or Bash terminal
- [ ] Azure Bicep CLI (`az bicep version`)

## Deployment Flow

```
┌─────────────────────────────────────────────┐
│  1. Setup Azure CLI & Authentication        │
│     az login                                 │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  2. Create Resource Group                   │
│     az group create -n rex-poker-coach-rg   │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  3. Create Container Registry (ACR)         │
│     az acr create -n rexregistryname        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  4. Build & Push Docker Image               │
│     docker build -t rex-poker-coach:latest  │
│     docker push to ACR                      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  5. Deploy Infrastructure with Bicep        │
│     az deployment group create              │
│     - Container Apps                        │
│     - PostgreSQL Flexible Server            │
│     - Storage Account                       │
│     - Application Insights                  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  6. Verify Deployment                       │
│     az containerapp logs show               │
│     curl https://<app-url>/health           │
└─────────────────────────────────────────────┘
```

## Step-by-Step Deployment

### Step 1: Authenticate with Azure

```bash
# Login to Azure
az login

# Set default subscription (optional)
az account set --subscription "Your-Subscription-ID"

# Verify authentication
az account show
```

### Step 2: Create Resource Group

```bash
# Create resource group
az group create \
  --name rex-poker-coach-rg \
  --location eastus

# Verify creation
az group show -n rex-poker-coach-rg
```

### Step 3: Create Container Registry

```bash
# Create Azure Container Registry
az acr create \
  --resource-group rex-poker-coach-rg \
  --name rexregistryname \
  --sku Basic \
  --admin-enabled true

# Get login credentials
az acr credential show \
  --resource-group rex-poker-coach-rg \
  --name rexregistryname
```

### Step 4: Build and Push Docker Image

```bash
# Build Docker image
docker build -t rex-poker-coach:latest .

# Tag image for ACR
docker tag rex-poker-coach:latest \
  rexregistryname.azurecr.io/rex-poker-coach:latest

# Login to ACR
az acr login --name rexregistryname

# Push image
docker push rexregistryname.azurecr.io/rex-poker-coach:latest

# Verify upload
az acr repository list --name rexregistryname
```

### Step 5: Deploy Infrastructure

```bash
# Update azure/parameters.json with your values:
# - location: eastus
# - environment: dev
# - containerRegistryName: rexregistryname

# Deploy Bicep template
az deployment group create \
  --resource-group rex-poker-coach-rg \
  --template-file azure/main.bicep \
  --parameters azure/parameters.json

# Monitor deployment
az deployment group show \
  --resource-group rex-poker-coach-rg \
  --name main \
  --query "properties.progressiveDeploymentStates[0].{time:timestamp, status:progressiveDeploymentStatus}" \
  --output table
```

### Step 6: Verify Deployment

```bash
# Get Container App details
az containerapp show \
  --resource-group rex-poker-coach-rg \
  --name rex-poker-coach-dev

# Get the application URL
az containerapp show \
  --resource-group rex-poker-coach-rg \
  --name rex-poker-coach-dev \
  --query properties.configuration.ingress.fqdn \
  --output tsv

# Test health endpoint
curl https://<app-url>/health

# View application logs
az containerapp logs show \
  --resource-group rex-poker-coach-rg \
  --name rex-poker-coach-dev \
  --tail 100
```

## Azure Resource Details

### Container Apps Environment
- **Name**: rex-poker-coach-env-dev
- **Log Analytics**: rex-poker-coach-logs-dev
- **Auto-scaling**: 1-3 replicas based on HTTP load

### Container App
- **Name**: rex-poker-coach-dev
- **Image**: rexregistryname.azurecr.io/rex-poker-coach:latest
- **Port**: 3001 (HTTP)
- **Health Probes**: Liveness & Readiness checks enabled

### PostgreSQL Server
- **Name**: rex-poker-coach-postgres-dev
- **Tier**: Burstable (Standard_B2s)
- **Storage**: 32 GB
- **Backup**: 7 days retention
- **Database**: PT4DB

### Storage Account
- **Name**: rexpokercoachdevsa
- **Kind**: StorageV2
- **Tier**: Standard LRS
- **File Share**: chromadb (100 GB quota)

### Monitoring
- **Application Insights**: rex-poker-coach-insights-dev
- **Log Analytics**: rex-poker-coach-logs-dev
- **Retention**: 30 days

## Environment Variables

The deployment configures these automatically:

```env
NODE_ENV=dev
API_PORT=3001
PT4_DB_HOST=rex-poker-coach-postgres-dev.postgres.database.azure.com
PT4_DB_NAME=PT4DB
PT4_DB_USER=postgres
PT4_DB_PASSWORD=[auto-generated]
CHROMA_URL=http://chromadb:8000
APPLICATIONINSIGHTS_CONNECTION_STRING=[auto-configured]
```

## Post-Deployment Configuration

### 1. Update Database Password
```bash
# In Azure Portal or via CLI, update the database password
az postgres flexible-server update \
  --resource-group rex-poker-coach-rg \
  --name rex-poker-coach-postgres-dev \
  --admin-password <new-password>
```

### 2. Configure Container App Environment
```bash
# Update environment variables
az containerapp update \
  --resource-group rex-poker-coach-rg \
  --name rex-poker-coach-dev \
  --set-env-vars PT4_DB_PASSWORD=<your-password>
```

### 3. Test API Endpoints
```bash
# Get app URL
APP_URL=$(az containerapp show \
  -g rex-poker-coach-rg \
  -n rex-poker-coach-dev \
  --query properties.configuration.ingress.fqdn \
  --output tsv)

# Test health
curl https://$APP_URL/health

# Sync hands (example)
curl -X POST https://$APP_URL/api/sync-hands \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'
```

## Cost Estimation

| Service | Tier | Est. Monthly |
|---------|------|--------------|
| Container Apps | Pay-as-you-go | ~$20-50 |
| PostgreSQL | Burstable B2s | ~$20-30 |
| Storage Account | Standard LRS | ~$5-10 |
| Application Insights | Pay-as-you-go | ~$0-5 |
| Log Analytics | Pay-as-you-go | ~$5-15 |
| **Total Estimate** | | **$50-110** |

*Costs vary by usage and region. Use Azure Pricing Calculator for exact estimates.*

## Troubleshooting

### Container App not starting
```bash
# Check container logs
az containerapp logs show -g rex-poker-coach-rg -n rex-poker-coach-dev

# Check revision status
az containerapp revision list -g rex-poker-coach-rg -n rex-poker-coach-dev

# Restart container
az containerapp update -g rex-poker-coach-rg -n rex-poker-coach-dev --restart
```

### Database connection issues
```bash
# Check PostgreSQL firewall rules
az postgres flexible-server firewall-rule list \
  -g rex-poker-coach-rg \
  --name rex-poker-coach-postgres-dev

# Allow Azure services
az postgres flexible-server firewall-rule create \
  -g rex-poker-coach-rg \
  --name rex-poker-coach-postgres-dev \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### Image pull errors
```bash
# Verify ACR login credentials
az acr credential show -n rexregistryname

# Re-push image if needed
docker push rexregistryname.azurecr.io/rex-poker-coach:latest

# Update container app image
az containerapp update \
  -g rex-poker-coach-rg \
  -n rex-poker-coach-dev \
  --image rexregistryname.azurecr.io/rex-poker-coach:latest
```

## Monitoring

### View Metrics
```bash
# CPU usage
az monitor metrics list \
  --resource /subscriptions/{subscription}/resourcegroups/rex-poker-coach-rg/providers/microsoft.app/containerapps/rex-poker-coach-dev \
  --metric CpuUsage

# Memory usage
az monitor metrics list \
  --resource /subscriptions/{subscription}/resourcegroups/rex-poker-coach-rg/providers/microsoft.app/containerapps/rex-poker-coach-dev \
  --metric MemoryUsage
```

### Set Up Alerts
```bash
# Example: Alert on high CPU (via Portal)
# 1. Go to Application Insights: rex-poker-coach-insights-dev
# 2. Alerts → New alert rule
# 3. Set condition: CPU > 80%
# 4. Configure action group (email/Slack)
```

## Clean Up

```bash
# Delete entire resource group (all resources)
az group delete -n rex-poker-coach-rg --yes

# Delete specific resource
az resource delete \
  --resource-group rex-poker-coach-rg \
  --name rex-poker-coach-dev \
  --resource-type Microsoft.App/containerApps
```

## Support & Resources

- [Azure Container Apps Docs](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Azure PostgreSQL Docs](https://learn.microsoft.com/en-us/azure/postgresql/)
- [Bicep Documentation](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Azure CLI Reference](https://learn.microsoft.com/en-us/cli/azure/reference-index)

---

**Your Rex Poker Coach is ready for production deployment on Azure! 🚀**
