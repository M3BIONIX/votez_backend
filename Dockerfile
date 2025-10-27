# Use Python 3.11 slim image as base
FROM python:3.11.7-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Set startup script permissions while still root
RUN chmod +x /app/docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Expose the port (Railway will provide PORT env variable)
EXPOSE 8000

# Set default port (will be overridden by Railway)
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:$PORT/')" || exit 1

# Run migrations and start the application
# Set PYTHONUNBUFFERED for better logging
ENV PYTHONUNBUFFERED=1

# Use the startup script
CMD ["/app/docker-entrypoint.sh"]
