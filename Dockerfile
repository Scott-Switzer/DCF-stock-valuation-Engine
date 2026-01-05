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

# Run the application (using Gunicorn for production)
CMD gunicorn --bind 0.0.0.0:$PORT api.index:app
