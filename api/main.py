"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Customer Intelligence API",
    description="Backend API for customer churn prediction and revenue risk management",
    version="0.1.0"
)

# CORS middleware
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "operational",
        "version": "0.1.0",
        "message": "Customer Intelligence API"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

# Import and include routers
# from routes import predictions, recommendations, customer, scenarios
# app.include_router(predictions.router)
# app.include_router(recommendations.router)
# app.include_router(customer.router)
# app.include_router(scenarios.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
