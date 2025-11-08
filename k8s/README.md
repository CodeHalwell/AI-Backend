# Kubernetes Manifests (`k8s/`)

Kubernetes deployment configurations for production environment.

## Files

### `namespace.yaml`

**What**: Kubernetes namespace for the application
**Why**: Isolates resources from other applications

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-backend
```

**Apply**:
```bash
kubectl apply -f k8s/namespace.yaml
```

### `deployment.yaml`

**What**: Application deployment with replicas and scaling
**Key Features**:
- **3 replicas**: High availability
- **Rolling updates**: Zero-downtime deployments
- **Resource limits**: CPU and memory constraints
- **Health checks**: Liveness and readiness probes
- **Auto-scaling**: HorizontalPodAutoscaler

**Configuration**:
- Min replicas: 3
- Max replicas: 10
- Target CPU: 70%
- Target Memory: 80%

**Apply**:
```bash
kubectl apply -f k8s/deployment.yaml
```

**Key Sections**:

#### Deployment Strategy
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1          # Add 1 new pod before removing old
    maxUnavailable: 0    # Keep all pods running during update
```

#### Resource Limits
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

#### Health Checks
```yaml
livenessProbe:   # Restart if unhealthy
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:  # Remove from load balancer if not ready
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

### `configmap.yaml`

**What**: Non-sensitive configuration
**Why**: Separates config from code

**Contains**:
- Redis URL
- Log level
- Worker count
- CORS origins

**Apply**:
```bash
kubectl apply -f k8s/configmap.yaml
```

**Update**:
```bash
# Edit ConfigMap
kubectl edit configmap ai-backend-config -n ai-backend

# Restart pods to pick up changes
kubectl rollout restart deployment/ai-backend -n ai-backend
```

### `secrets.yaml.example`

**What**: Template for sensitive data (API keys, passwords)
**Why**: Keep secrets out of git

**⚠️ SECURITY**: Never commit real secrets!

**Create secrets**:
```bash
kubectl create secret generic ai-backend-secrets \
  --from-literal=database-url='postgresql+asyncpg://...' \
  --from-literal=secret-key='your-secret-key' \
  --from-literal=openai-api-key='sk-...' \
  -n ai-backend
```

**Or from file**:
```bash
# Create .env file (don't commit!)
cat > .env.secrets << EOF
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=...
OPENAI_API_KEY=...
