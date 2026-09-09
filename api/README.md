# API Directory

FastAPI backend server for the Customer Intelligence Engine.

## Structure

```
api/
├── main.py              # FastAPI app entry point
├── routes/              # API route handlers
│   ├── predictions.py   # Churn prediction endpoints
│   ├── recommendations.py # Intervention recommendations
│   ├── customer.py      # Customer 360° endpoints
│   └── scenarios.py     # What-if simulator
├── models.py            # Pydantic request/response models
├── config.py            # API configuration
└── requirements.txt     # API-specific dependencies
```

## Running the API

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or run directly
python main.py
```

## API Endpoints (Planned)

### Health Check
- `GET /` - API status
- `GET /health` - Health check

### Predictions
- `GET /api/predictions/churn/{customer_id}` - Get churn probability for customer
- `POST /api/predictions/batch` - Batch churn predictions

### Recommendations
- `GET /api/recommendations/{customer_id}` - Get intervention recommendations
- `GET /api/recommendations/top-at-risk?limit=100` - Top at-risk customers

### Customer 360
- `GET /api/customer/{customer_id}` - Full customer profile
- `GET /api/customer/{customer_id}/timeline` - Customer event timeline
- `GET /api/customer/{customer_id}/metrics` - Customer KPIs

### Scenarios (What-if)
- `POST /api/scenarios/simulate` - Run scenario simulation
- `POST /api/scenarios/compare` - Compare scenarios

## Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Authentication (To Be Implemented)

- JWT token-based authentication
- API key for third-party integrations

## Deployment

- Docker: See `/Dockerfile`
- Render: See `/docs/DEPLOYMENT.md`
- AWS Lambda: FastAPI with Mangum adapter
