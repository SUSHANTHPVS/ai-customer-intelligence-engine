# 🚀 Deployment & Startup Guide

## Quick Start (Docker Compose)

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git (for cloning the repository)

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd AI\ Customer\ Intelligence\ Engine
```

### Step 2: Start Services
```bash
# Start all services (PostgreSQL, Backend API, Frontend)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Step 3: Access Application
- **Frontend Dashboard**: http://localhost
- **Backend API**: http://localhost:5000
- **Database**: localhost:5432

---

## Service Architecture

### 🗄️ PostgreSQL Database
- **Port**: 5432
- **Container**: ai-intelligence-db
- **Credentials**: postgres:sushanth123
- **Database**: customer_intelligence

### 🔧 Flask Backend API
- **Port**: 5000
- **Container**: ai-intelligence-api
- **Health Check**: http://localhost:5000/health
- **API Documentation**: http://localhost:5000/docs (if Swagger enabled)

### 🎨 React Frontend Dashboard
- **Port**: 80
- **Container**: ai-intelligence-frontend
- **Framework**: React + Vite + Tailwind CSS
- **Health Check**: http://localhost

---

## Dashboard Features

### 📊 Analytics Tab
- **Customer Segmentation**: Pie chart showing customer distribution across segments
- **Engagement Metrics**: Bar chart of customer engagement scores
- **LTV Predictions**: Line chart comparing predicted vs actual customer lifetime value
- **Churn Risk Analysis**: Table of high-risk customers with risk scores

### 📈 Model Metrics Tab
- **Model Accuracy**: Real-time accuracy percentage
- **Precision Score**: Model precision metric
- **Recall Score**: Model recall metric
- **Performance Over Time**: Line chart tracking metrics historical changes
- **Detailed Metrics**: Comprehensive metrics table with status indicators

---

## API Integration

### Base URL
```
http://backend:5000  (within Docker)
http://localhost:5000 (from host machine)
```

### Key Endpoints
- `GET /health` - Health check
- `GET /analytics/customer-segmentation` - Customer segments
- `GET /analytics/engagement-metrics` - Engagement data
- `GET /analytics/ltv-predictions` - LTV predictions
- `GET /analytics/churn-risk` - Churn risk analysis
- `GET /models/metrics` - Model performance metrics
- `GET /models/performance` - Historical performance data

### Response Format
```json
{
  "success": true,
  "data": { /* endpoint-specific data */ },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Development Setup

### Local Development (without Docker)

#### Backend
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-phase5.txt

# Run server
python phase5_api_server.py
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build
```

---

## Environment Variables

### Docker Compose (.env)
```
# Database
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=sushanth123
DB_NAME=customer_intelligence

# API
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=False

# Frontend
VITE_API_URL=http://localhost:5000

# Logging
LOG_LEVEL=INFO
```

### Frontend (frontend/.env or hardcoded in vite.config.js)
```
VITE_API_URL=http://localhost:5000
```

---

## Troubleshooting

### Services Won't Start
```bash
# Check service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Restart services
docker-compose restart

# Full reset (WARNING: deletes data)
docker-compose down -v
docker-compose up -d
```

### Frontend Can't Reach API
1. Check backend health: `curl http://localhost:5000/health`
2. Verify CORS settings in backend
3. Check VITE_API_URL environment variable
4. Verify Docker network: `docker network ls`

### Database Connection Issues
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Connect to database
docker exec -it ai-intelligence-db psql -U postgres -d customer_intelligence
```

### Port Already in Use
```bash
# Change ports in docker-compose.yml
# For example, change frontend port from 80 to 8080:
# ports:
#   - "8080:80"

docker-compose up -d
```

---

## Performance Monitoring

### Health Checks
Each service has built-in health checks:
- Backend: Checks `/health` endpoint every 30s
- Frontend: Checks HTTP response every 30s
- Database: Checks connectivity every 10s

### Logs
```bash
# Follow all logs
docker-compose logs -f

# Follow specific service
docker-compose logs -f backend

# View recent logs
docker-compose logs --tail 100 frontend
```

### Container Stats
```bash
docker stats
```

---

## Deployment Checklist

- [ ] Update `.env` file with production secrets
- [ ] Set `FLASK_ENV=production` in docker-compose.yml
- [ ] Configure SSL/HTTPS certificates
- [ ] Set up database backups
- [ ] Configure monitoring and alerting
- [ ] Set up CI/CD pipeline
- [ ] Test API endpoints thoroughly
- [ ] Verify frontend dashboard functionality
- [ ] Set up log aggregation
- [ ] Configure database replication (if needed)

---

## Security Notes

⚠️ **Before Production Deployment:**
1. Change default database password
2. Generate new SECRET_KEY
3. Enable SSL/HTTPS
4. Set up API authentication/authorization
5. Configure firewall rules
6. Set up database backups
7. Enable audit logging
8. Restrict CORS origins
9. Configure rate limiting
10. Implement API key management

---

## Useful Commands

```bash
# Build images without caching
docker-compose build --no-cache

# Scale services
docker-compose up -d --scale backend=3

# View container details
docker ps -a

# Access backend shell
docker exec -it ai-intelligence-api /bin/bash

# Access frontend shell
docker exec -it ai-intelligence-frontend /bin/sh

# View resource usage
docker stats ai-intelligence-api

# Prune unused resources
docker system prune -a
```

---

## Next Steps

1. **Customize Dashboard**: Add custom visualizations and reports
2. **Authentication**: Implement user login and role-based access
3. **Alerts**: Set up automated alerts for churn risk customers
4. **Integrations**: Connect with CRM, marketing platforms
5. **Scaling**: Set up load balancing and auto-scaling
6. **Monitoring**: Deploy Prometheus + Grafana stack

---

**For more information, see:**
- [PHASE5_API_DOCUMENTATION.md](../PHASE5_API_DOCUMENTATION.md)
- [ARCHITECTURE_OVERVIEW.md](../ARCHITECTURE_OVERVIEW.md)
- [Docker Documentation](https://docs.docker.com/)
- [React Documentation](https://react.dev/)
