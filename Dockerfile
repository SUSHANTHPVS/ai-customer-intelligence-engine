# Stage 1: Base image with Python
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-phase5.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-phase5.txt

# Copy application files
COPY phase5_api_server.py .
COPY cache.py extensions.py auth.py customers_bp.py jobs.py export_bp.py realtime.py rbac.py audit.py admin_bp.py twofa.py webhooks_bp.py import_bp.py graphql_bp.py insights.py datasets_bp.py ml_bp.py cohort_bp.py .
COPY models/ ./models/

# Expose port
EXPOSE 5000

# Environment variables
ENV FLASK_APP=phase5_api_server.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD-SHELL curl -f http://localhost:${PORT:-5000}/health || exit 1

# Run the application
CMD ["python", "phase5_api_server.py"]
