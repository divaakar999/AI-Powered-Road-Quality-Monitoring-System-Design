# 🚀 Deploy Road Quality Monitor to Streamlit Cloud - Quick Start

## 5-Minute Deployment

### Step 1: Verify Your Repository

```bash
# Ensure you're in the workspace root
cd d:\workspace\road

# Check required files exist
ls road_quality_monitor/streamlit_app.py
ls road_quality_monitor/requirements.txt
ls road_quality_monitor/.streamlit/config.toml
ls road_quality_monitor/road_quality_monitor/4_dashboard/dashboard_main.py
```

### Step 3: Verify requirements.txt

Streamlit Cloud uses the **root `requirements.txt`** file. Make sure it's optimized for Streamlit:

```bash
# Check that these libraries are in requirements.txt
grep -E "(streamlit|ultralytics|opencv-python-headless)" requirements.txt
```

✅ **Should contain:**
- `streamlit>=1.28.0`
- `ultralytics>=8.1.0`
- `opencv-python-headless>=4.8.0` (NOT `opencv-python`)
- `numpy<2.0.0`
- `torch` (installed automatically by ultralytics)

⚠️ **Should NOT contain:**
- `torch==2.0.1` (too old, use latest via ultralytics)
- `psycopg2-binary` (requires PostgreSQL system libs)
- `fastapi` (only needed for backend)

**For FastAPI backend deployment** (Render), use: `requirements.backend.txt`

### Step 3: Commit & Push to GitHub

```bash
cd d:\workspace\road

# Stage all changes
git add .

# Commit
git commit -m "feat: Add Streamlit Cloud deployment configuration

- STREAMLIT_DEPLOYMENT.md: Complete deployment guide
- .streamlit/config.toml: Cloud optimized configuration
- requirements.txt: Streamlit-optimized dependencies

Streamlit app ready to deploy to share.streamlit.io"

# Push to GitHub
git push origin main
```

### Step 4: Deploy on Streamlit Cloud (2 minutes)

**Option A: Auto-Deploy (Recommended)**

1. Go to https://share.streamlit.io
2. Sign up with GitHub (if not already done)
3. Click **"New app"**
4. Select:
   - **Repository:** `your-username/AI-Powered-Road-Quality-Monitoring-System-Design`
   - **Branch:** `main`
   - **Main file path:** `road_quality_monitor/streamlit_app.py`
5. Click **"Deploy!"** ✨
6. Wait for build (~2-3 minutes)
7. **Your app is live!** 🎉

**Option B: Via Streamlit CLI (Local Testing)**

```bash
# Test locally first
cd d:\workspace\road
streamlit run road_quality_monitor/streamlit_app.py

# This opens: http://localhost:8501
```

### Step 5: Access Your Live Dashboard

**Your app URL:**
```
https://<your-github-username>-road-quality-monitor.streamlit.app
```

Example: `https://divaakar999-road-quality-monitor.streamlit.app`

---

## 🎯 What Gets Deployed

Your Streamlit app includes:

✅ **Live Dashboard**
- 🎥 Real-time detection visualization
- 🗺️ Interactive Folium maps
- 📊 Analytics & statistics
- 📄 PDF report generation

✅ **File Upload Support**
- Single image detection
- Batch image processing
- Video frame analysis

✅ **YOLOv8 Integration**
- Auto-loads pretrained model
- Runs inference on Streamlit Cloud

---

## ⚠️ Cloud Limitations & Solutions

| Limitation | Impact | Solution |
|------------|--------|----------|
| **1 GB RAM** | Large model loads slowly | Use model caching (already done) |
| **No display** | No webcam video input (initially) | Use `streamlit-webrtc` (included) |
| **Auto-sleep 48h** | App goes offline if unused | Upgrade to Pro tier ($5/mo) |
| **Upload limit 200MB** | Can't upload huge videos | Use smaller files or upgrade |

---

## 🔍 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'dashboard_main'"

**Solution:**
```python
# In road_quality_monitor/streamlit_app.py, ensure these lines are at top:
sys.path.insert(0, str(ROOT / "road_quality_monitor"))
sys.path.insert(0, str(ROOT / "road_quality_monitor" / "3_detection"))
sys.path.insert(0, str(ROOT / "road_quality_monitor" / "4_dashboard"))
```

### Problem: App takes forever to load

**Why:** First run downloads YOLOv8 model (~100 MB)  
**Solution:** Wait ~5 minutes on first load, then it's cached

### Problem: Webcam not working

**Why:** Browser security + Streamlit Cloud setup  
**Solution:** Already handled by `streamlit-webrtc>=0.47.0` in requirements

### Problem: "opencv failed to load"

**Why:** Used wrong OpenCV package  
**Solution:** Ensure requirements.txt has:
```
opencv-python-headless>=4.8.0
```
NOT `opencv-python`

---

## 📚 For More Details

See full deployment guide: [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md)

Topics covered:
- Advanced configuration
- Environment variables & secrets
- Performance optimization
- Scaling & tier upgrades
- Monitoring & logging
- Migration to custom deployment

---

## ✅ Deployment Checklist

Before clicking "Deploy":

- [ ] Code pushed to GitHub (`git push origin main`)
- [ ] `requirements.txt` includes `streamlit>=1.28.0`
- [ ] `.streamlit/config.toml` exists
- [ ] `streamlit_app.py` is in `road_quality_monitor/` directory
- [ ] No large files in `.gitignore` (except `*.pt`, `weights/`)
- [ ] App tested locally: `streamlit run road_quality_monitor/streamlit_app.py`

---

## 🎉 Success!

Once deployed, you can:

✅ Share URL with team: `https://<username>-road-quality-monitor.streamlit.app`  
✅ Embed in website: `<iframe src="..."/>`  
✅ Monitor via Streamlit Cloud dashboard  
✅ Update app by pushing to GitHub (auto-redeploys!)

---

**Estimated Deployment Time:** 5 minutes ⏱️  
**Cost:** Free ✨  
**Next Step:** Share your live dashboard with stakeholders!
