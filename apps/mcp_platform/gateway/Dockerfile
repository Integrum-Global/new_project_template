# Multi-stage build for MCP Enterprise Gateway
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 gateway

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/gateway/.local

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/logs /app/data /app/certs && \
    chown -R gateway:gateway /app

# Switch to non-root user
USER gateway

# Add local bin to PATH
ENV PATH=/home/gateway/.local/bin:$PATH

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV GATEWAY_CONFIG_PATH=/app/config/gateway.yaml

# Expose ports
EXPOSE 8000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the gateway
CMD ["python", "-m", "mcp_enterprise_gateway.gateway.core.server"]
