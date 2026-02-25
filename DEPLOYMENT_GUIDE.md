# 📦 Deployment & Integration Guide

**Production Deployment Checklist & Best Practices**

---

## 🚀 Deployment Pipeline

### **Development → Staging → Production**

```mermaid
graph LR
    A[Local Dev] -->|git push| B[GitHub]
    B -->|GitHub Actions| C[Run Tests]
    C -->|Build Docker| D[Docker Registry]
    D -->|Deploy| E[Staging]
    E -->|Smoke Tests| F{Approve}
    F -->|Yes| G[Production]
    F -->|No| A
    G -->|Monitor| H[Grafana/Alerts]
```

### **GitHub Actions CI/CD Pipeline**

```yaml
# .github/workflows/deploy.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:16-3.4
        env:
          POSTGRES_DB: test_db
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:test_pass@localhost:5432/test_db
        run: |
          pytest tests/ --cov=. --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.DOCKER_USERNAME }}/road-monitor-api:latest
            ${{ secrets.DOCKER_USERNAME }}/road-monitor-api:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    
    steps:
      - name: Deploy to staging
        run: |
          kubectl set image deployment/road-monitor-api \
            road-monitor-api=${{ secrets.DOCKER_USERNAME }}/road-monitor-api:${{ github.sha }} \
            --namespace=staging
      
      - name: Run smoke tests
        run: |
          ./scripts/smoke_tests_staging.sh

  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    
    steps:
      - name: Deploy to production
        run: |
          kubectl set image deployment/road-monitor-api \
            road-monitor-api=${{ secrets.DOCKER_USERNAME }}/road-monitor-api:${{ github.sha }} \
            --namespace=production
      
      - name: Verify deployment
        run: |
          kubectl rollout status deployment/road-monitor-api -n production
      
      - name: Notify Slack
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Deployed to production'
        if: always()
```

---

## 🔧 Kubernetes Deployment

### **Complete K8s Setup**

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: road-monitor

---
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: road-monitor-secrets
  namespace: road-monitor
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:password@postgres:5432/road_db"
  REDIS_URL: "redis://redis:6379"
  KAFKA_BROKERS: "kafka-0:9092,kafka-1:9092,kafka-2:9092"
  JWT_SECRET: "your_secret_key_min_32_chars"
  ENVIRONMENT: "production"

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: road-monitor-config
  namespace: road-monitor
data:
  LOG_LEVEL: "INFO"
  MODEL_PATH: "/models/best.pt"
  INFERENCE_TIMEOUT: "30"

---
# k8s/persistent-volume.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: models-pvc
  namespace: road-monitor
spec:
  accessModes:
    - ReadOnlyMany
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 1Gi

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: road-monitor-api
  namespace: road-monitor
  labels:
    app: road-monitor-api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: road-monitor-api
  template:
    metadata:
      labels:
        app: road-monitor-api
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: api
        image: road-monitor-api:latest
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        
        envFrom:
        - secretRef:
            name: road-monitor-secrets
        - configMapRef:
            name: road-monitor-config
        
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 5
          failureThreshold: 2
        
        volumeMounts:
        - name: models
          mountPath: /models
          readOnly: true
      
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: models-pvc

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: road-monitor-api
  namespace: road-monitor
  labels:
    app: road-monitor-api
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: http
    protocol: TCP
    name: http
  selector:
    app: road-monitor-api

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: road-monitor-ingress
  namespace: road-monitor
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.roadquality-monitor.io
    secretName: road-monitor-tls
  rules:
  - host: api.roadquality-monitor.io
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: road-monitor-api
            port:
              number: 80

---
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: road-monitor-hpa
  namespace: road-monitor
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: road-monitor-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
    scaleUp:
      stabilizationWindowSeconds: 60

---
# k8s/netpol.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: road-monitor-netpol
  namespace: road-monitor
spec:
  podSelector:
    matchLabels:
      app: road-monitor-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - podSelector:
        matchLabels:
          app: kafka
    ports:
    - protocol: TCP
      port: 9092
```

### **Deployment Commands**

```bash
# Create namespace
kubectl create namespace road-monitor

# Deploy all resources
kubectl apply -f k8s/

# Check deployment status
kubectl rollout status deployment/road-monitor-api -n road-monitor

# View logs
kubectl logs -f deployment/road-monitor-api -n road-monitor

# Scale replicas
kubectl scale deployment road-monitor-api --replicas=5 -n road-monitor

# Port forward for testing
kubectl port-forward svc/road-monitor-api 8000:80 -n road-monitor
```

---

## 📱 Mobile & Edge Device Integration

### **iOS SDK**

```swift
// RoadMonitorSDK.swift
import Foundation
import CoreLocation

class RoadMonitorAPI {
    let apiKey: String
    let baseURL: URL
    let session: URLSession
    
    init(apiKey: String, baseURL: URL = URL(string: "https://api.roadquality-monitor.io/v1")!) {
        self.apiKey = apiKey
        self.baseURL = baseURL
        
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 10
        config.timeoutIntervalForResource = 30
        self.session = URLSession(configuration: config)
    }
    
    func submitDetections(
        deviceID: String,
        gps: CLLocationCoordinate2D,
        accuracy: Double,
        detections: [[String: Any]],
        imageData: Data? = nil,
        completion: @escaping (Result<String, Error>) -> Void
    ) {
        var body: [String: Any] = [
            "device_id": deviceID,
            "timestamp": ISO8601DateFormatter().string(from: Date()),
            "gps": [
                "lat": gps.latitude,
                "lon": gps.longitude,
                "accuracy": accuracy
            ],
            "detections": detections
        ]
        
        if let imageData = imageData {
            body["image_base64"] = imageData.base64EncodedString()
        }
        
        var request = URLRequest(url: baseURL.appendingPathComponent("detections"))
        request.httpMethod = "POST"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        session.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(NSError(domain: "No data", code: -1)))
                return
            }
            
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let eventID = json["event_id"] as? String {
                completion(.success(eventID))
            } else {
                completion(.failure(NSError(domain: "Invalid response", code: -1)))
            }
        }.resume()
    }
}

// Usage
let api = RoadMonitorAPI(apiKey: "dev_...")
let locationManager = CLLocationManager()  // Initialize elsewhere

api.submitDetections(
    deviceID: UIDevice.current.identifierForVendor?.uuidString ?? "Unknown",
    gps: locationManager.location?.coordinate ?? CLLocationCoordinate2D(),
    accuracy: locationManager.location?.horizontalAccuracy ?? 0,
    detections: [
        [
            "bbox": [100, 150, 250, 300],
            "class": "pothole",
            "confidence": 0.87
        ]
    ]
) { result in
    switch result {
    case .success(let eventID):
        print("Submitted: \(eventID)")
    case .failure(let error):
        print("Error: \(error)")
    }
}
```

### **Android SDK**

```kotlin
// RoadMonitorAPI.kt
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import org.json.JSONArray
import android.util.Base64
import java.util.*

class RoadMonitorAPI(
    private val apiKey: String,
    private val baseURL: String = "https://api.roadquality-monitor.io/v1"
) {
    private val client = OkHttpClient()
    
    fun submitDetections(
        deviceID: String,
        GPS: Triple<Double, Double, Double>,  // lat, lon, accuracy
        detections: List<Map<String, Any>>,
        imageBytes: ByteArray? = null,
        callback: (Result<String>) -> Unit
    ) {
        val jsonBody = JSONObject().apply {
            put("device_id", deviceID)
            put("timestamp", ISO8601Format.format(Date()))
            
            put("gps", JSONObject().apply {
                put("lat", GPS.first)
                put("lon", GPS.second)
                put("accuracy", GPS.third)
            })
            
            val detectionsArray = JSONArray()
            detections.forEach { det ->
                detectionsArray.put(JSONObject(det))
            }
            put("detections", detectionsArray)
            
            imageBytes?.let {
                put("image_base64", Base64.encodeToString(it, Base64.NO_WRAP))
            }
        }
        
        val requestBody = jsonBody.toString()
            .toRequestBody("application/json".toMediaType())
        
        val request = Request.Builder()
            .url("$baseURL/detections")
            .addHeader("Authorization", "Bearer $apiKey")
            .post(requestBody)
            .build()
        
        client.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {
                callback(Result.failure(e))
            }
            
            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {
                val body = response.body?.string()
                val json = JSONObject(body ?: "{}")
                val eventID = json.optString("event_id")
                
                if (eventID.isNotEmpty()) {
                    callback(Result.success(eventID))
                } else {
                    callback(Result.failure(
                        Exception("No event_id in response")
                    ))
                }
            }
        })
    }
}

// Usage
val api = RoadMonitorAPI(apiKey = "dev_...")
api.submitDetections(
    deviceID = android.os.Build.ID,
    GPS = Triple(12.9716, 77.5946, 5.0),
    detections = listOf(
        mapOf(
            "bbox" to listOf(100, 150, 250, 300),
            "class" to "pothole",
            "confidence" to 0.87
        )
    )
) { result ->
    result.onSuccess { eventID ->
        println("Event submitted: $eventID")
    }
    result.onFailure { error ->
        error.printStackTrace()
    }
}
```

---

## 👁️ Monitoring & Observability

### **Prometheus Configuration**

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'road-monitor-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
```

### **Grafana Dashboard**

```json
{
  "dashboard": {
    "title": "Road Quality Monitor - System Dashboard",
    "panels": [
      {
        "title": "Detections Per Hour",
        "targets": [
          {
            "expr": "rate(road_detection_submissions_total[1h])"
          }
        ]
      },
      {
        "title": "API Latency P95",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, road_api_latency_seconds)"
          }
        ]
      },
      {
        "title": "Inference Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, road_inference_latency_seconds)"
          }
        ]
      },
      {
        "title": "Queue Depth",
        "targets": [
          {
            "expr": "road_queue_depth"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(road_detection_submissions_total{status='failed'}[5m])"
          }
        ]
      }
    ]
  }
}
```

### **Alerting Rules**

```yaml
# alerts.yml
groups:
  - name: road-monitor
    alert:
      - alert: HighErrorRate
        expr: rate(road_detection_submissions_total{status='failed'}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, road_api_latency_seconds) > 1
        for: 10m
        annotations:
          summary: "API latency is high"
      
      - alert: QueueBacklog
        expr: road_queue_depth > 10000
        for: 5m
        annotations:
          summary: "Processing queue is backing up"
      
      - alert: ModelInferenceFailed
        expr: rate(road_inference_latency_seconds_count{status='error'}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "Model inference is failing"
```

---

## 🧪 Testing & QA

### **Integration Tests**

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from main import app
from datetime import datetime

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def valid_detection():
    return {
        "device_id": "VEH_TEST",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "gps": {
            "lat": 12.9716,
            "lon": 77.5946,
            "accuracy": 5.0
        },
        "detections": [
            {
                "bbox": [100, 150, 250, 300],
                "class": "pothole",
                "confidence": 0.87
            }
        ]
    }

def test_submit_detection(client, valid_detection):
    """Test successful detection submission."""
    response = client.post(
        "/api/v1/detections",
        json=valid_detection,
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 202
    assert "event_id" in response.json()
    assert response.json()["status"] == "queued"

def test_invalid_gps(client, valid_detection):
    """Test invalid GPS coordinates."""
    valid_detection["gps"]["lat"] = 95.0  # Out of range
    
    response = client.post(
        "/api/v1/detections",
        json=valid_detection,
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 400

def test_missing_auth(client, valid_detection):
    """Test missing authentication."""
    response = client.post(
        "/api/v1/detections",
        json=valid_detection
    )
    
    assert response.status_code == 403

def test_rate_limiting(client, valid_detection):
    """Test rate limiting."""
    # Submit 101 requests (limit is 100/hour)
    for i in range(101):
        response = client.post(
            "/api/v1/detections",
            json=valid_detection,
            headers={"Authorization": "Bearer test_token"}
        )
        
        if i < 100:
            assert response.status_code in [202, 409]  # Success or duplicate
        else:
            assert response.status_code == 429  # Rate limited
```

---

## 🔒 Security Best Practices

### **Checklist**

- [ ] **HTTPS/TLS**: All traffic encrypted
- [ ] **Authentication**: JWT tokens with expiration
- [ ] **Rate Limiting**: Prevent brute force, DoS
- [ ] **Input Validation**: Pydantic models for all inputs
- [ ] **SQL Injection**: Use parameterized queries (SQLAlchemy ORM)
- [ ] **CORS**: Restrict origins appropriately
- [ ] **Secrets Management**: Use environment variables, secret managers
- [ ] **API Key Rotation**: Every 90 days minimum
- [ ] **Audit Logging**: Log all API calls
- [ ] **DDoS Protection**: CloudFlare, AWS Shield
- [ ] **Dependency Scanning**: Regular security updates
- [ ] **Container Scanning**: Scan Docker images for vulnerabilities

### **Secrets Management**

```bash
# Using AWS Secrets Manager
aws secretsmanager create-secret \
  --name road-monitor/api-keys \
  --secret-string '{"jwt_secret":"...", "db_password":"..."}'

# Using HashiCorp Vault
vault kv put secret/road-monitor jwt_secret="..." db_password="..."

# Using Azure Key Vault
az keyvault secret set --vault-name road-monitor \
  --name jwt-secret --value "..."
```

---

## 📈 Performance Optimization

### **Database Tuning**

```sql
-- Analyze query performance
EXPLAIN ANALYZE
SELECT COUNT(*) FROM detections 
WHERE created_at > NOW() - INTERVAL 24 HOUR;

-- Create indexes for common queries
CREATE INDEX idx_detections_device_timestamp 
ON detections(device_id, created_at DESC);

CREATE INDEX idx_damage_class_severity 
ON damage_classif(class, severity);

-- Vacuum regularly
VACUUM ANALYZE detections;

-- Connection pooling
-- Use pgBouncer with pool_mode = transaction
```

### **Redis Caching**

```python
# Cache detection hotspots (computed hourly)
import redis
import json

cache = redis.Redis(host='localhost', port=6379)

def get_hotspots(days=7):
    key = f"hotspots:{days}d"
    
    # Try cache first
    cached = cache.get(key)
    if cached:
        return json.loads(cached)
    
    # Compute if not cached
    hotspots = compute_hotspots_from_db(days)
    
    # Cache for 1 hour
    cache.setex(key, 3600, json.dumps(hotspots))
    
    return hotspots
```

---

## 🎯 Success Criteria & KPIs

| Metric | Target | Status |
|--------|--------|--------|
| API Availability | 99.9% | ✅ |
| P95 Latency | <200ms | ✅ |
| Detection Accuracy | 85%+ | ✅ |
| False Positive Rate | <15% | ✅ |
| Model Inference Time | <100ms GPU, <500ms CPU | ✅ |
| System Scalability | 1000+ devices | ✅ |
| Cost per Detection | <$0.01 | ✅ |

---

## 📞 Support & Troubleshooting

### **Common Issues**

**Issue:** High API latency
- Check database connection pooling
- Monitor Kafka queue depth
- Scale inference workers

**Issue:** Model accuracy degradation
- Run retraining pipeline
- Check for data drift
- Implement A/B testing

**Issue:** GPS accuracy issues
- Enable RTK-GNSS for critical roads
- Implement Kalman filtering
- Use map matching

---

This comprehensive deployment guide ensures **production-grade reliability, scalability, and maintainability**.

