# 🎯 Deployment Checklist & Quick Reference

## ✅ Pre-Deployment Checklist

### System Requirements
- [ ] Docker Engine 20.10+ installed
- [ ] Docker Compose 2.0+ installed
- [ ] 4GB+ available RAM
- [ ] 50GB+ available disk space
- [ ] Port 80, 5000, 5432 available

### Code & Configuration
- [ ] All dependencies in `requirements-phase5.txt` listed
- [ ] Frontend dependencies in `package.json` complete
- [ ] `.env` file configured with correct credentials
- [ ] `docker-compose.yml` updated with all services
- [ ] `Dockerfile` exists in project root
- [ ] `frontend/Dockerfile` created for React build
- [ ] All API endpoints return expected data format

### Frontend Setup
- [ ] React components created (AnalyticsDashboard, ModelMetricsDashboard)
- [ ] Zustand store configured (dashboardStore.js)
- [ ] API client with interceptors set up
- [ ] Health status component implemented
- [ ] Charts library (Recharts) configured
- [ ] Tailwind CSS styling complete
- [ ] Responsive design tested

### Backend Verification
- [ ] Flask API server running locally
- [ ] All endpoints tested with Postman/curl
- [ ] Database migrations completed
- [ ] Model files accessible
- [ ] Logging configured
- [ ] Health check endpoint working

### Database
- [ ] PostgreSQL 13+ running
- [ ] Database `customer_intelligence` created
- [ ] Tables and schema verified
- [ ] Sample data loaded
- [ ] Backup strategy in place

---

## 🚀 Quick Start Commands

### Windows (PowerShell)
```powershell
# Navigate to project directory
cd "C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine"

# Run startup script
.\start.ps1

# Select option 1 to start all services
```

### Linux/Mac (Bash)
```bash
# Navigate to project directory
cd ~/Desktop/AI\ Customer\ Intelligence\ Engine

# Make script executable
chmod +x start.sh

# Run startup script
./start.sh

# Select option 1 to start all services
```

### Manual Docker Commands
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps

# Stop services
docker-compose down

# Full reset
docker-compose down -v
```

---

## 📋 Service Status Commands

### Check Individual Services
```bash
# Backend health
curl http://localhost:5000/health

# Frontend status
curl http://localhost

# Database connectivity
docker exec ai-intelligence-db pg_isready -U postgres -d customer_intelligence

# Docker status
docker ps
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs

# Backend only
docker-compose logs backend

# Frontend only
docker-compose logs frontend

# Database only
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f
```

---

## 🌐 Access Points

| Service | URL | Port | Purpose |
|---------|-----|------|---------|
| Frontend Dashboard | http://localhost | 80 | React Dashboard UI |
| Backend API | http://localhost:5000 | 5000 | REST API Server |
| Database | localhost | 5432 | PostgreSQL |
| Health Check (Backend) | http://localhost:5000/health | 5000 | API Status |

---

## 🔧 Troubleshooting Quick Guide

### Problem: Can't Connect to API
```bash
# Check if backend is running
docker ps | grep backend

# View backend logs
docker-compose logs backend

# Test endpoint directly
curl -v http://localhost:5000/health

# Check network
docker network ls
docker network inspect ai-intelligence-network
```

### Problem: Frontend Shows Error
```bash
# Check frontend logs
docker-compose logs frontend

# Verify environment variable
docker exec ai-intelligence-frontend env | grep VITE

# Check browser console for errors
# F12 → Console tab

# Verify API connection
curl http://localhost:5000/health
```

### Problem: Database Connection Failed
```bash
# Check if database is running
docker ps | grep postgres

# Test connection
docker exec ai-intelligence-db psql -U postgres -d customer_intelligence -c "\dt"

# Check database logs
docker-compose logs postgres

# Reset database
docker-compose down -v postgres
docker-compose up -d postgres
```

### Problem: Port Already in Use
```bash
# Find process using port 80
# Windows: netstat -ano | findstr :80
# Linux/Mac: sudo lsof -i :80

# Change port in docker-compose.yml
# ports:
#   - "8080:80"  # Change 80 to 8080

# Restart services
docker-compose restart
```

### Problem: Out of Memory
```bash
# Check resource usage
docker stats

# Limit container resources in docker-compose.yml
# deploy:
#   resources:
#     limits:
#       memory: 2G

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

---

## 📊 Dashboard Quick Navigation

### Analytics Tab
1. **KPI Cards** - Top 3 metrics at a glance
   - Total Customers
   - Engagement Score
   - Churn Risk Count

2. **Customer Segmentation** - Pie chart showing distribution
   - Click chart for segment details

3. **Engagement Metrics** - Bar chart
   - Compare different metrics
   - Hover for exact values

4. **LTV Predictions** - Line chart
   - Predicted vs Actual values
   - Trend analysis

5. **Churn Risk Table** - High-risk customers
   - Risk score displayed
   - Sort and filter capability

### Model Metrics Tab
1. **KPI Cards**
   - Accuracy percentage
   - Precision score
   - Recall score

2. **Performance Chart** - Historical trends
   - Multiple metrics on one chart
   - Date range visible on X-axis

3. **Detailed Metrics Table**
   - Individual metric values
   - Status indicators
   - Trend direction and percentage

---

## 🔐 Security Checklist

Before Production:
- [ ] Change default database password
- [ ] Generate new SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Implement API authentication
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable audit logging
- [ ] Test error handling

---

## 📈 Performance Optimization

### Docker Optimization
```bash
# Build with BuildKit
export DOCKER_BUILDKIT=1
docker build .

# Use .dockerignore to reduce image size
# Verify image size
docker images

# Remove dangling images
docker image prune
```

### Frontend Optimization
```bash
# Check bundle size
npm run build

# Analyze dependencies
npm list

# Remove unused packages
npm prune
```

### Database Optimization
```bash
# Create indexes
docker exec ai-intelligence-db psql -U postgres -d customer_intelligence -c "CREATE INDEX idx_customer_id ON table_name(customer_id);"

# Analyze query performance
EXPLAIN ANALYZE SELECT ...
```

---

## 🆘 Getting Help

### Documentation
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Detailed deployment instructions
- [frontend/README.md](./frontend/README.md) - Frontend documentation
- [PHASE5_API_DOCUMENTATION.md](./PHASE5_API_DOCUMENTATION.md) - API reference
- [ARCHITECTURE_OVERVIEW.md](./ARCHITECTURE_OVERVIEW.md) - System architecture

### Log Files
```bash
# Docker logs
docker-compose logs backend > backend.log
docker-compose logs frontend > frontend.log
docker-compose logs postgres > database.log

# Application logs (in container)
docker exec ai-intelligence-api cat /app/logs/api.log
```

### Common Issues
1. **API not responding** → Check backend health: `curl http://localhost:5000/health`
2. **Frontend can't connect** → Verify VITE_API_URL environment variable
3. **Database errors** → Check PostgreSQL logs: `docker-compose logs postgres`
4. **Port conflicts** → Change ports in docker-compose.yml
5. **Memory issues** → Increase Docker memory allocation

---

## 📞 Support Contact Information

For issues:
1. Check logs: `docker-compose logs`
2. Review documentation
3. Verify service status: `docker ps`
4. Test connectivity: `curl http://localhost:5000/health`
5. Contact DevOps team with log files

---

**Last Updated**: 2024-01-15  
**Version**: 1.0.0  
**Maintainer**: AI Intelligence Team
