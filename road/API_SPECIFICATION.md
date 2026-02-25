# 🔌 Backend API Specification & Implementation Guide

**Road Quality Monitoring System – REST API for IoT & Mobile Integration**

---

## 📡 API Overview

### **Base URL**
```
Production:  https://api.roadquality-monitor.io/v1
Development: http://localhost:8000/v1
```

### **Authentication**
```
Type: Bearer Token (JWT)
Header: Authorization: Bearer {token}
Expires: 24 hours
Scope: read:detections, write:detections, read:analytics
```

### **Rate Limiting**
```
Free tier:     100 req/hour per device_id
Professional:  10,000 req/hour per device_id
Enterprise:    Unlimited

Limit headers in response:
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 2026-02-25T11:45:00Z
```

---

## 📋 Detailed API Endpoints

### **1. Detection Submission**

#### **Endpoint: POST /api/v1/detections**

Submit real-time road damage detections with GPS coordinates.

**Request:**
```yaml
Headers:
  Content-Type: application/json
  Authorization: Bearer {jwt_token}

Body:
  {
    "device_id": "VEH_001",              # Vehicle/camera identifier
    "timestamp": "2026-02-25T10:30:45Z", # ISO8601 UTC
    "gps": {
      "lat": 12.9716,                    # Latitude (degrees)
      "lon": 77.5946,                    # Longitude (degrees)
      "accuracy": 5.0,                   # ±5 meters
      "altitude": 920.5,                 # Meters above sea level
      "heading": 45.2,                   # Compass bearing 0-360°
      "speed": 45.5                      # km/h
    },
    "detections": [
      {
        "bbox": [100, 150, 250, 300],    # [x1, y1, x2, y2] pixels
        "class": "pothole",               # "pothole" | "crack" | "wear"
        "confidence": 0.87,               # 0.0-1.0
        "class_id": 0                     # 0=pothole, 1=crack, 2=wear
      },
      {
        "bbox": [450, 200, 600, 310],
        "class": "crack",
        "confidence": 0.72,
        "class_id": 1
      }
    ],
    "metadata": {
      "camera_id": "CAM_001",
      "video_source": "dashcam",         # Source identifier
      "road_type": "highway",            # "highway" | "urban" | "rural"
      "weather": "clear"                 # Optional condition
    },
    "frame": {
      "width": 1280,
      "height": 720,
      "format": "H264"                   # Video codec (if video)
    },
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEA..."  # Optional: base64 image
  }

Response (202 Accepted):
  {
    "event_id": "evt_550e8400e29b41d4a716446655440000",
    "status": "queued",                  # "queued" | "processing" | "completed"
    "processing_eta_seconds": 5,
    "created_at": "2026-02-25T10:30:46Z",
    "message": "Detection queued for processing"
  }

Error Responses:
  400 Bad Request:
    {
      "error": "INVALID_REQUEST",
      "message": "Missing required field: gps.lat",
      "details": {"field": "gps.lat", "reason": "required"}
    }
  
  401 Unauthorized:
    {
      "error": "UNAUTHORIZED",
      "message": "Invalid or expired token"
    }
  
  409 Conflict (Duplicate):
    {
      "error": "DUPLICATE_DETECTION",
      "message": "Similar detection already recorded",
      "details": {
        "existing_event_id": "evt_...",
        "distance_m": 8.5,
        "time_diff_sec": 12
      }
    }
  
  429 Too Many Requests:
    {
      "error": "RATE_LIMIT_EXCEEDED",
      "message": "100 requests per hour limit reached",
      "retry_after_seconds": 3600
    }
  
  503 Service Unavailable:
    {
      "error": "SERVICE_UNAVAILABLE",
      "message": "Processing queue is full, try again in 30 seconds",
      "retry_after_seconds": 30
    }
```

**Example cURL:**
```bash
curl -X POST "https://api.roadquality-monitor.io/v1/detections" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "VEH_001",
    "timestamp": "2026-02-25T10:30:45Z",
    "gps": {"lat": 12.9716, "lon": 77.5946, "accuracy": 5.0},
    "detections": [{"bbox": [100, 150, 250, 300], "class": "pothole", "confidence": 0.87}]
  }'
```

**Python SDK:**
```python
import requests
from datetime import datetime

class RoadMonitorAPI:
    def __init__(self, api_key, base_url="https://api.roadquality-monitor.io/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def submit_detections(self, device_id, gps, detections, image_base64=None):
        """Submit road damage detections."""
        payload = {
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "gps": gps,
            "detections": detections,
            "image_base64": image_base64
        }
        
        response = self.session.post(
            f"{self.base_url}/detections",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 202:
            return response.json()
        elif response.status_code == 409:
            print(f"Duplicate detection: {response.json()}")
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limited. Retry after {retry_after} seconds")
        
        return response.json()

# Usage
api = RoadMonitorAPI(api_key="your_jwt_token_here")
response = api.submit_detections(
    device_id="VEH_001",
    gps={"lat": 12.9716, "lon": 77.5946, "accuracy": 5.0},
    detections=[
        {"bbox": [100, 150, 250, 300], "class": "pothole", "confidence": 0.87}
    ]
)
print(f"Event ID: {response['event_id']}")
```

---

### **2. Get Detection Status**

#### **Endpoint: GET /api/v1/detections/{event_id}**

Poll the status and results of a submitted detection.

**Response:**
```yaml
200 OK:
  {
    "event_id": "evt_550e8400e29b41d4a716446655440000",
    "status": "completed",               # "queued" | "processing" | "completed" | "failed"
    "device_id": "VEH_001",
    "created_at": "2026-02-25T10:30:46Z",
    "processed_at": "2026-02-25T10:30:51Z",
    "processing_time_ms": 5000,
    
    "detections": [                      # Only in "completed" status
      {
        "detection_id": "det_...",
        "bbox": [100, 150, 250, 300],
        "class": "pothole",
        "confidence": 0.87,
        "severity": "HIGH",              # HIGH | MEDIUM | LOW
        "severity_score": 0.78,          # 0.0-1.0
        "repair_priority": 1,            # 1=urgent, 3=routine
        "estimated_size_m2": 0.45
      }
    ],
    
    "location": {
      "lat": 12.9716,
      "lon": 77.5946,
      "address": "Bangalore-Mysore Highway, KM 45",  # Reverse geocoding
      "road_type": "highway"
    }
  }

404 Not Found:
  {
    "error": "NOT_FOUND",
    "message": "Event not found or expired"
  }
```

---

### **3. Batch Query by Location**

#### **Endpoint: GET /api/v1/detections/location**

Query all detections within a geographic bounding box.

**Query Parameters:**
```yaml
lat_min: 12.90                # South boundary
lat_max: 13.00                # North boundary
lon_min: 77.50                # West boundary
lon_max: 77.60                # East boundary
severity: HIGH,MEDIUM         # Optional filter (comma-separated)
class: pothole,crack          # Optional filter
days: 7                        # Optional: last N days (default: 7)
limit: 100                     # Max results (default: 100, max: 1000)
offset: 0                      # Pagination offset
```

**Response:**
```yaml
200 OK:
  {
    "query": {
      "bounds": {"lat_min": 12.90, "lat_max": 13.00, "lon_min": 77.50, "lon_max": 77.60},
      "filters": {"severity": ["HIGH"], "class": ["pothole"]},
      "time_range": "last 7 days"
    },
    "results": {
      "total": 45,
      "returned": 45,
      "detections": [
        {
          "detection_id": "det_001",
          "location": {"lat": 12.9716, "lon": 77.5946},
          "class": "pothole",
          "severity": "HIGH",
          "confidence": 0.87,
          "timestamp": "2026-02-25T10:30:45Z",
          "address": "Bangalore-Mysore Highway, KM 45"
        },
        ...
      ]
    },
    "pagination": {
      "has_next": false,
      "next_offset": null
    }
  }
```

---

### **4. Analytics & Statistics**

#### **Endpoint: GET /api/v1/analytics/summary**

Real-time system statistics and damage overview.

**Response:**
```yaml
200 OK:
  {
    "timestamp": "2026-02-25T10:35:00Z",
    
    "summary": {
      "total_detections": 12547,
      "last_7_days": 1240,
      "last_24_hours": 185,
      "active_devices": 87
    },
    
    "severity_breakdown": {
      "HIGH": {"count": 185, "percentage": 14.9},
      "MEDIUM": {"count": 480, "percentage": 38.7},
      "LOW": {"count": 575, "percentage": 46.4}
    },
    
    "class_breakdown": {
      "pothole": {"count": 520, "percentage": 41.9},
      "crack": {"count": 480, "percentage": 38.7},
      "wear": {"count": 240, "percentage": 19.4}
    },
    
    "detection_trend": {
      "last_24h": [
        {"hour": "2026-02-24T11:00Z", "count": 8},
        {"hour": "2026-02-24T12:00Z", "count": 15},
        {"hour": "2026-02-24T13:00Z", "count": 12},
        ...
      ],
      "rolling_avg_per_hour": 7.7
    },
    
    "top_hotspots": [
      {
        "rank": 1,
        "location": {"lat": 12.9716, "lon": 77.5946},
        "address": "Bangalore-Mysore Highway, KM 45",
        "detection_count": 45,
        "severity_high_pct": 45.5,
        "last_detection": "2026-02-25T09:15:00Z"
      },
      ...
    ],
    
    "health": {
      "api_latency_p95_ms": 120,
      "api_error_rate_pct": 0.2,
      "queue_depth": 245,
      "inference_latency_p95_ms": 95
    }
  }
```

---

### **5. Report Generation**

#### **Endpoint: POST /api/v1/reports/generate**

Generate a maintenance report for geographic area.

**Request:**
```yaml
{
  "name": "Bangalore Maintenance Report Q1 2026",
  "bounds": {
    "lat_min": 12.90,
    "lat_max": 13.00,
    "lon_min": 77.50,
    "lon_max": 77.60
  },
  "severity_filter": ["HIGH", "MEDIUM"],  # Include only these severities
  "start_date": "2026-01-01",
  "end_date": "2026-03-31",
  "format": "pdf",                        # "pdf" | "csv" | "json"
  "include_maps": true,
  "include_cost_analysis": true
}

Response (202 Accepted):
{
  "report_id": "rpt_550e8400...",
  "status": "generating",
  "download_url": "https://api.../reports/rpt_550e8400.pdf",
  "estimated_completion_seconds": 30
}

# Get report status
GET /api/v1/reports/{report_id}
Response:
{
  "report_id": "rpt_550e8400...",
  "status": "completed",                 # "generating" | "completed" | "failed"
  "created_at": "2026-02-25T10:40:00Z",
  "completed_at": "2026-02-25T10:41:15Z",
  "file_size_bytes": 2500000,
  "download_url": "https://api.../reports/rpt_550e8400.pdf",
  "expires_at": "2026-03-01T10:41:15Z"  # 4 days retention
}
```

---

### **6. Device Management**

#### **Endpoint: GET /api/v1/devices**

List all registered devices/vehicles.

**Response:**
```yaml
200 OK:
  {
    "devices": [
      {
        "device_id": "VEH_001",
        "name": "Bangalore Patrol Car #1",
        "status": "online",              # "online" | "offline" | "inactive"
        "last_heartbeat": "2026-02-25T10:35:12Z",
        "gps_last_position": {"lat": 12.9716, "lon": 77.5946},
        "detections_total": 245,
        "detections_last_24h": 18,
        "api_version": "1.0.0",
        "created_at": "2026-01-15T00:00:00Z"
      },
      ...
    ]
  }
```

#### **Endpoint: POST /api/v1/devices**

Register a new device.

**Request:**
```yaml
{
  "device_id": "VEH_002",
  "name": "Bangalore Patrol Car #2",
  "device_type": "dashcam",             # "dashcam" | "smartphone" | "embedded"
  "camera_specs": {
    "resolution": "1920x1080",
    "fps": 30,
    "sensor_size_mp": 12
  },
  "organization_id": "ORG_BANGALORE"
}

Response (201 Created):
{
  "device_id": "VEH_002",
  "api_key": "dev_550e8400e29b41d4a716446655440000",
  "created_at": "2026-02-25T10:45:00Z",
  "message": "Device registered successfully. Use api_key for authentication."
}
```

---

## 🔐 Authentication & Security

### **JWT Token Generation**

```python
from datetime import datetime, timedelta
import jwt

def generate_token(device_id, organization_id, secret_key, expires_in_hours=24):
    """Generate JWT token for device authentication."""
    payload = {
        "device_id": device_id,
        "org_id": organization_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
        "scopes": ["read:detections", "write:detections", "read:analytics"]
    }
    
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

# Usage
token = generate_token(
    device_id="VEH_001",
    organization_id="ORG_BANGALORE",
    secret_key="your_secret_key_min_32_chars"
)
print(f"Token: {token}")
```

### **HTTPS & TLS**

```
Required:
✅ TLS 1.2 or higher
✅ Certificate pinning (prevent MITM attacks)
✅ HSTS headers (enforce HTTPS)
```

### **API Key Rotation**

```
Every 90 days:
1. Generate new key
2. Distribute to all devices
3. Deprecate old key (grace period: 30 days)
4. Monitor for failures
5. Revoke old key after grace period
```

---

## 📦 SDK & Client Libraries

### **Python SDK**

```bash
pip install road-quality-monitor
```

```python
from road_quality_monitor import RoadMonitorAPI
import cv2

api = RoadMonitorAPI(api_key="dev_...")

# Capture frame from camera
cap = cv2.VideoCapture(0)
ret, frame = cap.read()

# Run detection
from ultralytics import YOLO
model = YOLO("best.pt")
results = model(frame)

# Convert to API format
detections = []
for box in results[0].boxes:
    detection = {
        "bbox": [int(x) for x in box.xyxy[0].tolist()],
        "class": results[0].names[int(box.cls)],
        "confidence": float(box.conf)
    }
    detections.append(detection)

# Submit
response = api.submit_detections(
    device_id="VEH_001",
    gps={"lat": 12.9716, "lon": 77.5946, "accuracy": 5.0},
    detections=detections
)

print(f"Submitted event: {response['event_id']}")
```

### **JavaScript SDK**

```bash
npm install road-quality-monitor
```

```javascript
import RoadMonitorAPI from 'road-quality-monitor';

const api = new RoadMonitorAPI({
  apiKey: 'dev_...',
  baseURL: 'https://api.roadquality-monitor.io/v1'
});

async function submitDetection() {
  const response = await api.detections.create({
    device_id: 'VEH_001',
    gps: {
      lat: 12.9716,
      lon: 77.5946,
      accuracy: 5.0
    },
    detections: [
      {
        bbox: [100, 150, 250, 300],
        class: 'pothole',
        confidence: 0.87
      }
    ]
  });
  
  console.log(`Event submitted: ${response.event_id}`);
}
```

---

## 🧪 Testing & Debugging

### **Postman Collection**

```json
{
  "info": {
    "name": "Road Quality Monitor API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Submit Detection",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{api_key}}"
          },
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"device_id\": \"VEH_001\",\n  \"timestamp\": \"{{$isoTimestamp}}\",\n  \"gps\": {\"lat\": 12.9716, \"lon\": 77.5946, \"accuracy\": 5.0},\n  \"detections\": [{\"bbox\": [100, 150, 250, 300], \"class\": \"pothole\", \"confidence\": 0.87}]\n}"
        },
        "url": {
          "raw": "{{base_url}}/detections",
          "host": ["{{base_url}}"],
          "path": ["detections"]
        }
      }
    }
  ]
}
```

### **Mock Server for Testing**

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_submit_detection(client):
    """Test detection submission."""
    payload = {
        "device_id": "VEH_TEST",
        "timestamp": "2026-02-25T10:30:45Z",
        "gps": {"lat": 12.9716, "lon": 77.5946, "accuracy": 5.0},
        "detections": [{"bbox": [100, 150, 250, 300], "class": "pothole", "confidence": 0.87}]
    }
    
    response = client.post(
        "/api/v1/detections",
        json=payload,
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 202
    assert "event_id" in response.json()
```

---

## 📊 Monitoring & Logging

### **Structured Logging**

```python
import json
import logging
from datetime import datetime

class JsonLogger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def log_detection(self, event_id, device_id, detections_count, processing_time_ms):
        """Log detection submission in structured format."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "detection_submitted",
            "event_id": event_id,
            "device_id": device_id,
            "detections_count": detections_count,
            "processing_time_ms": processing_time_ms,
            "status": "success"
        }
        self.logger.info(json.dumps(log_entry))

# Elasticsearch indexing (via Logstash)
# Query: GET /detections-*-*/_search
# {"query": {"match": {"device_id": "VEH_001"}}}
# → All events for VEH_001 in past 30 days
```

### **Metrics Collection**

```python
from prometheus_client import Counter, Histogram, Gauge

detections_submitted = Counter(
    'road_detections_submitted_total',
    'Total detections submitted',
    ['class', 'severity']
)

detection_latency = Histogram(
    'road_detection_latency_seconds',
    'Detection processing latency'
)

inference_latency = Histogram(
    'road_inference_latency_seconds',
    'YOLOv8 inference time'
)

queue_depth = Gauge(
    'road_queue_depth',
    'Current processing queue size'
)

# Usage
detections_submitted.labels(class_='pothole', severity='HIGH').inc()
with detection_latency.time():
    process_detection(payload)
```

---

## 💡 Implementation Best Practices

### **Request Validation**

```python
from pydantic import BaseModel, validator

class GPSData(BaseModel):
    lat: float
    lon: float
    accuracy: float
    
    @validator('lat')
    def validate_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @validator('lon')
    def validate_lon(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v
    
    @validator('accuracy')
    def validate_accuracy(cls, v):
        if v < 0:
            raise ValueError('Accuracy must be positive')
        return v
```

### **Error Handling**

```python
from fastapi import HTTPException

@app.post("/api/v1/detections")
async def submit_detection(payload: DetectionPayload):
    try:
        # Validate GPS accuracy
        if payload.gps.accuracy > 100:  # >100m is unreliable
            raise HTTPException(
                status_code=400,
                detail="GPS accuracy poor. Minimum 100m required"
            )
        
        # Check for duplicates
        if is_duplicate(payload):
            raise HTTPException(
                status_code=409,
                detail="Similar detection already recorded"
            )
        
        # Queue for processing
        event_id = await queue_detection(payload)
        return {"event_id": event_id, "status": "queued"}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### **Concurrent Request Handling**

```python
from fastapi import BackgroundTasks
import asyncio

@app.post("/api/v1/detections")
async def submit_detection(payload: DetectionPayload, background_tasks: BackgroundTasks):
    """
    Accept request immediately, process in background.
    Returns event_id for polling.
    """
    event_id = str(uuid4())
    
    # Enqueue to Kafka
    await kafka_producer.send_and_wait(
        "events/road-damage",
        {
            "event_id": event_id,
            "payload": payload.dict()
        }
    )
    
    # Schedule heavy processing in background
    background_tasks.add_task(process_detection, event_id, payload)
    
    return {"event_id": event_id, "status": "queued", "processing_eta_seconds": 5}
```

---

## 🚀 Deployment Checklist

- [ ] API keys generated for all devices
- [ ] HTTPS/TLS certificates installed
- [ ] Database replicas configured
- [ ] Redis cache cluster running
- [ ] Kafka brokers operational
- [ ] Load balancer health checks passing
- [ ] Monitoring alerts configured
- [ ] Rate limiting rules tested
- [ ] Backup/restore procedures tested
- [ ] Documentation deployed to client portal

