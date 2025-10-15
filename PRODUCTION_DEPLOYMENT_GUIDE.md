# Production Deployment Guide

This guide covers deploying the Agno MCP Orchestration System in a production environment with proper scalability, monitoring, and reliability.

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10 or higher
- Redis server (for caching)
- API keys for Tavily and/or Jina
- Docker (optional, for containerized deployment)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-server.git
cd mcp-server

# Install dependencies
pip install -r requirements.txt

# Install production dependencies
pip install redis asyncio-mqtt prometheus-client

# Copy production configuration
cp production.env.example .env
```

### 3. Configuration

Edit `.env` file with your production settings:

```bash
# Required API keys
TAVILY_API_KEY=your_actual_tavily_key
JINA_API_KEY=your_actual_jina_key

# Rate limiting (adjust based on your needs)
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
MAX_CONCURRENT_REQUESTS=100

# Redis configuration
REDIS_URL=redis://your-redis-server:6379

# Memory management
MAX_EXECUTION_HISTORY=1000
MAX_REQUEST_SIZE_MB=10
```

## 🏗️ Architecture Options

### Option 1: Single Server Deployment

```bash
# Run production server
python -m src.production_server
```

**Pros:**
- Simple setup
- Low resource requirements
- Easy to maintain

**Cons:**
- Single point of failure
- Limited scalability
- No load balancing

### Option 2: Containerized Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install redis asyncio-mqtt prometheus-client

# Copy application code
COPY src/ ./src/
COPY production.env.example .env

# Create non-root user
RUN useradd -m -u 1000 agno && chown -R agno:agno /app
USER agno

# Expose port (if using HTTP mode)
EXPOSE 8000

# Run the application
CMD ["python", "-m", "src.production_server"]
```

Build and run:

```bash
# Build image
docker build -t agno-production .

# Run container
docker run -d \
  --name agno-server \
  --env-file .env \
  -p 8000:8000 \
  agno-production
```

### Option 3: Kubernetes Deployment

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agno-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agno-server
  template:
    metadata:
      labels:
        app: agno-server
    spec:
      containers:
      - name: agno-server
        image: agno-production:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: TAVILY_API_KEY
          valueFrom:
            secretKeyRef:
              name: agno-secrets
              key: tavily-api-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: agno-service
spec:
  selector:
    app: agno-server
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 📊 Monitoring and Observability

### 1. Health Checks

The production server provides several health check endpoints:

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed system status
curl http://localhost:8000/status

# Metrics endpoint
curl http://localhost:8000/metrics
```

### 2. Logging

Production logs are structured and include:

- Request/response times
- Rate limiting events
- Cache hit/miss ratios
- Error rates and types
- Memory usage statistics

```bash
# View logs
tail -f agno_production.log

# Filter for errors
grep "ERROR" agno_production.log

# Monitor rate limiting
grep "Rate limit" agno_production.log
```

### 3. Metrics Collection

Key metrics to monitor:

- **Request Rate**: Requests per second/minute
- **Response Time**: P50, P95, P99 latencies
- **Success Rate**: Percentage of successful requests
- **Cache Hit Rate**: Percentage of cache hits
- **Memory Usage**: Current memory consumption
- **Active Connections**: Number of concurrent requests

### 4. Alerting

Set up alerts for:

- High error rate (>5%)
- High response time (>5 seconds)
- Memory usage (>80%)
- Cache hit rate (<50%)
- Rate limit violations

## 🔧 Performance Tuning

### 1. Rate Limiting Tuning

Adjust based on your API limits and usage patterns:

```bash
# For high-traffic applications
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_PER_HOUR=2000
MAX_CONCURRENT_REQUESTS=200

# For API-limited scenarios
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500
MAX_CONCURRENT_REQUESTS=50
```

### 2. Memory Optimization

```bash
# Reduce memory usage
MAX_EXECUTION_HISTORY=500
CLEANUP_INTERVAL_SECONDS=180

# Increase for high-memory scenarios
MAX_EXECUTION_HISTORY=2000
CLEANUP_INTERVAL_SECONDS=600
```

### 3. Caching Strategy

```bash
# Short TTL for dynamic content
CACHE_TTL_SECONDS=1800  # 30 minutes

# Long TTL for static content
CACHE_TTL_SECONDS=7200  # 2 hours

# Disable caching for testing
CACHE_TTL_SECONDS=0
```

## 🛡️ Security Considerations

### 1. API Key Management

- Store API keys in environment variables or secret management systems
- Never commit API keys to version control
- Rotate keys regularly
- Use different keys for different environments

### 2. Rate Limiting

- Implement client-based rate limiting
- Use different limits for different client types
- Monitor for abuse patterns
- Implement IP-based blocking for malicious clients

### 3. Input Validation

- Validate all input parameters
- Sanitize user queries
- Implement query length limits
- Block malicious patterns

### 4. Network Security

- Use HTTPS for all communications
- Implement proper CORS policies
- Use firewall rules to restrict access
- Monitor for suspicious traffic patterns

## 📈 Scaling Strategies

### 1. Horizontal Scaling

- Deploy multiple instances behind a load balancer
- Use Redis for shared caching
- Implement session affinity if needed
- Monitor resource usage per instance

### 2. Vertical Scaling

- Increase CPU and memory resources
- Optimize database connections
- Tune garbage collection settings
- Monitor resource utilization

### 3. Caching Strategy

- Use Redis for distributed caching
- Implement cache warming strategies
- Monitor cache hit rates
- Implement cache invalidation policies

## 🔄 Backup and Recovery

### 1. Configuration Backup

```bash
# Backup configuration
cp .env config-backup-$(date +%Y%m%d).env

# Backup Redis data
redis-cli --rdb backup-$(date +%Y%m%d).rdb
```

### 2. Log Rotation

```bash
# Set up log rotation
sudo logrotate -f /etc/logrotate.d/agno
```

### 3. Disaster Recovery

- Maintain configuration backups
- Document recovery procedures
- Test recovery processes regularly
- Implement monitoring for service availability

## 🧪 Load Testing

### 1. Using k6

Create `load-test.js`:

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 10 },
    { duration: '5m', target: 10 },
    { duration: '2m', target: 20 },
    { duration: '5m', target: 20 },
    { duration: '2m', target: 0 },
  ],
};

export default function() {
  let response = http.post('http://localhost:8000/api/search', JSON.stringify({
    query: 'test query',
    max_results: 5
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 5000ms': (r) => r.timings.duration < 5000,
  });
  
  sleep(1);
}
```

Run load test:

```bash
k6 run load-test.js
```

### 2. Using Apache JMeter

1. Create a test plan
2. Add HTTP Request samplers
3. Configure thread groups
4. Add response assertions
5. Run the test

## 📋 Production Checklist

### Pre-Deployment

- [ ] API keys configured and tested
- [ ] Redis server running and accessible
- [ ] Environment variables set correctly
- [ ] Logging configuration verified
- [ ] Health checks working
- [ ] Load testing completed
- [ ] Security review completed

### Post-Deployment

- [ ] Monitor system metrics
- [ ] Verify rate limiting is working
- [ ] Check cache performance
- [ ] Monitor error rates
- [ ] Verify logging is working
- [ ] Test failover procedures
- [ ] Document any issues

### Ongoing Maintenance

- [ ] Regular security updates
- [ ] Monitor performance metrics
- [ ] Review and tune configuration
- [ ] Backup configuration and data
- [ ] Update documentation
- [ ] Conduct disaster recovery tests

## 🆘 Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Check execution history size
   - Verify cleanup intervals
   - Monitor for memory leaks

2. **Rate Limiting Issues**
   - Check rate limit configuration
   - Monitor client request patterns
   - Adjust limits if needed

3. **Cache Performance**
   - Verify Redis connectivity
   - Check cache hit rates
   - Monitor cache memory usage

4. **API Errors**
   - Check API key validity
   - Monitor external API status
   - Verify timeout settings

### Debug Commands

```bash
# Check system status
python -m src.production_server --status

# View detailed logs
tail -f agno_production.log | grep ERROR

# Test cache connectivity
redis-cli ping

# Monitor system resources
htop
iostat -x 1
```

## 📞 Support

For production support:

1. Check the logs first
2. Verify configuration
3. Test individual components
4. Review monitoring metrics
5. Contact support with detailed information

---

This guide provides a comprehensive foundation for deploying the Agno MCP Orchestration System in production. Adjust the configuration and deployment strategy based on your specific requirements and constraints.
