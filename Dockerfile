FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose Port (Render/Railway use $PORT, default to 5000)
ENV PORT=5000
EXPOSE 5000

# Gunicorn tuning for I/O-bound workloads:
# - 4 workers for multi-core utilization
# - 4 threads per worker for concurrent I/O
# - 30s timeout to prevent hung requests
# - Access log for monitoring
CMD gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 4 --timeout 30 --access-logfile - app:app
