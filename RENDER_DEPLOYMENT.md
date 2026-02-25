# 🚀 Render Deployment Guide

**Deploy Road Quality Monitoring System to Render (Production-Ready Backend + API)**

---

## 📋 Prerequisites

✅ GitHub account with repository
✅ Render account (https://render.com)
✅ Model weights file (`best.pt` - 40MB)
✅ Credit card for Render (free tier available)

---

## 🎯 Render Deployment Architecture

```
GitHub Repository
    ↓ (Auto-deploy on push)
Render Services:
├─ Web Service (FastAPI API)          → Public API endpoint
├─ PostgreSQL Database                → Data persistence
├─ Redis Cache                        → Session/cache layer
└─ Worker (Inference Pipeline)        → Background processing
```

---

## 📍 Step 1: Prepare Your Repository

Before deploying, ensure all files are pushed to GitHub:

```bash
git add .
git commit -m "chore: Add Render deployment configuration"
git push origin main
```

**Required files in repo:**
- ✅ `Dockerfile` (FastAPI app)
- ✅ `Dockerfile.worker` (Inference worker)
- ✅ `Dockerfile.postgres` (Database)
- ✅ `Dockerfile.redis` (Cache)
- ✅ `render.yaml` (Configuration)
- ✅ `Procfile` (Alternative deployment)
- ✅ `requirements.txt` (Python dependencies)
- ✅ `main.py` (FastAPI application)
- ✅ `workers/inference_worker.py` (Background worker)
- ✅ `.env.example` (Environment template)

---

## 🔑 Step 2: Set Up Render Account

1. **Create Render account** → https://render.com/register
2. **Connect GitHub** → Authorize Render to access your repositories
3. **Create dashboard** → https://dashboard.render.com

---

## 🗄️ Step 3: Deploy Database (PostgreSQL)

### Option A: Using Render Dashboard

1. Go to **Render Dashboard** → **New** → **PostgreSQL**
2. **Configuration:**
   ```
   Name: road-monitor-db
   Database: road_db
   User: postgres
   Region: Choose closest to you
   Plan: Free tier ($0/month, limited) or Starter ($7/month)
   ```
3. **Create** → Copy connection string
4. **Initialize database:**
   ```bash
   psql "your_connection_string" < init_db.sql
   ```

### Option B: Using render.yaml (Recommended)

**Already included in render.yaml** ✅

---

## 💾 Step 4: Deploy Redis Cache

### Using Render Dashboard

1. Go to **New** → **Redis**
2. **Configuration:**
   ```
   Name: road-monitor-redis
   Region: Same as DB
   Plan: Free tier or Starter ($7/month)
   ```
3. **Create** → Copy connection string

### Using render.yaml

**Already included** ✅

---

## 🔌 Step 5: Deploy API Service

### Using Render Dashboard

1. Go to **New** → **Web Service**
2. **Configuration:**
   ```
   Name: road-monitor-api
   Environment: Docker
   Repository: https://github.com/divaakar999/AI-Powered-Road-Quality-Monitoring-System-Design
   Root Directory: (leave empty)
   Dockerfile: ./Dockerfile
   Build Command: (leave empty - auto-detected)
   Start Command: uvicorn main:app --host 0.0.0.0 --port 8000
   Plan: Starter ($7/month)
   Instances: 1 (can scale later)
   ```

3. **Add Environment Variables:**
   ```
   DATABASE_URL = (from PostgreSQL connection string)
   REDIS_URL = (from Redis connection string)
   JWT_SECRET = (cryptographically generate)
   ENVIRONMENT = production
   LOG_LEVEL = INFO
   WORKERS = 4
   ```

4. **Deploy** → Wait 5-10 minutes for build

### Using render.yaml (Recommended)

```bash
# Deploy all services at once from render.yaml
```

See **Step 7** below.

---

## 👷 Step 6: Deploy Worker Service

1. Go to **New** → **Background Worker**
2. **Configuration:**
   ```
   Name: road-monitor-inference
   Environment: Docker
   Repository: (same as API)
   Dockerfile: ./Dockerfile.worker
   Start Command: python workers/inference_worker.py
   Plan: Standard ($12/month)
   ```

3. **Add Environment Variables:**
   ```
   DATABASE_URL = (from PostgreSQL)
   REDIS_URL = (from Redis)
   JWT_SECRET = (same as API)
   MODEL_PATH = /models/best.pt
   ENVIRONMENT = production
   ```

4. **Deploy**

---

## 🚀 Step 7: Deploy All Services with render.yaml

**Faster alternative: Deploy everything at once**

### A. Using Render CLI

```bash
# Install Render CLI
npm install -g render

# Login
render login

# Deploy from render.yaml
render deploy --path ./render.yaml
```

### B. Using Dashboard

1. Go to Render Dashboard
2. Click **New** → **Infrastructure as Code**
3. Connect repository
4. Select `main` branch
5. Paste `render.yaml` content
6. Click **Create**

Render will automatically:
- Create PostgreSQL instance
- Create Redis instance
- Build and deploy API
- Build and deploy Worker
- Configure networking

---

## 📝 Step 8: Configure Environment Variables

### Via Render Dashboard

For **each service** (API, Worker):

1. Go to service settings
2. **Environment** tab
3. Add variables:
   - `DATABASE_URL` = PostgreSQL connection string
   - `REDIS_URL` = Redis connection string
   - `JWT_SECRET` = (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
   - `ENVIRONMENT` = production
   - `LOG_LEVEL` = INFO

### Secure Secrets

**Never commit .env files to GitHub!**

```bash
# Local development only
cp .env.example .env
# Edit .env with real values
echo ".env" >> .gitignore
```

---

## ✅ Step 9: Verify Deployment

### Check API Health

```bash
# Get your API URL from Render Dashboard (e.g., https://road-monitor-api.onrender.com)
curl https://road-monitor-api.onrender.com/health

# Expected response:
# {"status": "ok", "version": "1.0.0", "timestamp": "2026-02-25T..."}
```

### Test Detection API

```bash
curl -X POST https://road-monitor-api.onrender.com/api/v1/detections \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "VEH_001",
    "timestamp": "2026-02-25T10:30:45Z",
    "gps": {"lat": 12.9716, "lon": 77.5946, "accuracy": 5.0},
    "detections": [{"bbox": [100, 150, 250, 300], "class": "pothole", "confidence": 0.87}]
  }'
```

### View Logs

In Render Dashboard:
1. Select service (API or Worker)
2. **Logs** tab
3. View real-time output

---

## 🔄 Step 10: Set Up Auto-Deployment

1. In Render Dashboard → Service Settings
2. **Deploy** tab
3. Enable **Auto-Deploy**:
   ```
   Branch: main
   ```

Now, every push to `main` will automatically redeploy!

---

## 📊 Monitoring & Observability

### View Metrics

1. Service → **Metrics** tab:
   - CPU usage
   - Memory usage
   - Network I/O
   - Restarts

### Set Up Alerts

1. Service → **Alerts** tab
2. Create alert for:
   - High CPU (>80%)
   - High memory (>512MB)
   - Service down
   - Build failures

### View Logs

1. Service → **Logs** tab
2. Stream real-time output
3. Search for errors

---

## 💵 Cost Estimation

| Service | Type | Price | Notes |
|---------|------|-------|-------|
| **API** | Web (Starter) | $7/month | Includes 750 free hours/month |
| **Database** | PostgreSQL Starter | $15/month | 1GB storage |
| **Redis** | Starter | $7/month | 250MB DB size |
| **Worker** | Standard | $12/month | Continuous background job |
| **Total** | | ~$41/month | For production workload |

**Free tier available** for testing (with limitations)

---

## 🔐 Security Best Practices

### 1. Enable HTTPS
✅ Automatic (Render provides SSL cert)

### 2. Set JWT Secret
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Protect Environment Variables
- Use Render's environment variables (encrypted)
- Never commit `.env` to GitHub
- Rotate secrets every 90 days

### 4. Database Security
- Use strong password
- Enable SSL connections
- Restrict IP whitelist (if available)

### 5. API Rate Limiting
- Configured in FastAPI
- 100 requests/hour per device

---

## 🆘 Troubleshooting

### Issue: "Build failed"
**Solution:**
- Check Logs tab for errors
- Verify `Dockerfile` syntax
- Ensure all dependencies in `requirements.txt`
- Check Python version (should be 3.10+)

### Issue: "Service keeps restarting"
**Solution:**
- Check memory usage (might be OOM)
- Review application logs
- Verify environment variables are set
- Database connection string correct?

### Issue: "Database connection refused"
**Solution:**
- Copy connection string directly from Render
- Ensure PostgreSQL instance is running
- Check `DATABASE_URL` in environment variables
- Run `init_db.sql` to initialize schema

### Issue: "Inference worker timing out"
**Solution:**
- Increase worker memory allocation
- Check model file path (`/models/best.pt`)
- Verify Kafka/Redis connectivity
- Monitor worker logs

### Issue: "API responding slowly"
**Solution:**
- Scale to more instances (API → Settings → Scaling)
- Check database query performance
- Monitor Redis cache hit rate
- Upgrade to higher plan

---

## 📈 Scaling for Production

### Horizontal Scaling (More Instances)

**API Service:**
```
Settings → Scaling → Max instances: 3+
```

**Cost:** +$7/month per instance

### Vertical Scaling (More Resources)

**Upgrade plan:**
```
Starter ($7) → Standard ($12) → Professional ($19)
```

---

## 🔄 Continuous Deployment

### Auto-Deploy on GitHub Push

1. Render Dashboard → Service Settings
2. **Deploys** tab → **Auto-deploy**
3. Select branch: `main`

Now every commit to `main` branch triggers deployment!

### Manual Deployment

1. Service → **Manual Deploy**
2. Click **Deploy latest commit**

---

## 🧪 Testing Production API

### Python Client

```python
import requests

BASE_URL = "https://road-monitor-api.onrender.com"
API_KEY = "dev_..."

def submit_detection(gps, detections):
    response = requests.post(
        f"{BASE_URL}/api/v1/detections",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "device_id": "VEH_001",
            "timestamp": "2026-02-25T10:30:45Z",
            "gps": gps,
            "detections": detections
        }
    )
    return response.json()

# Test
result = submit_detection(
    gps={"lat": 12.9716, "lon": 77.5946, "accuracy": 5.0},
    detections=[{
        "bbox": [100, 150, 250, 300],
        "class": "pothole",
        "confidence": 0.87
    }]
)
print(f"Event: {result['event_id']}")
```

### cURL

```bash
curl -X GET https://road-monitor-api.onrender.com/health
```

---

## 📞 Getting Help

- **Render Docs:** https://render.com/docs
- **API Docs:** https://{your-api}.onrender.com/docs (interactive)
- **Health Check:** https://{your-api}.onrender.com/health
- **GitHub Issues:** Post in repository

---

## ✅ Deployment Checklist

- [ ] Repository pushed to GitHub
- [ ] All Dockerfiles created
- [ ] requirements.txt updated
- [ ] render.yaml configured
- [ ] Render account created
- [ ] GitHub connected to Render
- [ ] Database deployed & initialized
- [ ] Redis deployed
- [ ] API deployed & health check passing
- [ ] Worker deployed
- [ ] Environment variables set
- [ ] Auto-deployment enabled
- [ ] API tested with curl/Postman
- [ ] Monitoring configured
- [ ] Custom domain configured (optional)

---

## 🎉 Success! Your API is Live!

**Your API is now running at:**
```
https://road-monitor-api.onrender.com
```

**Swagger UI Documentation:**
```
https://road-monitor-api.onrender.com/docs
```

**ReDoc Documentation:**
```
https://road-monitor-api.onrender.com/redoc
```

---

**Next Steps:**
1. Test API endpoints
2. Set up monitoring
3. Configure custom domain (optional)
4. Add webhook integrations
5. Scale as needed

Happy deploying! 🚀
