# Multi-stage build for MCP Tools Server
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 mcp

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=mcp:mcp . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs && \
    chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    MCP_SERVER_NAME=mcp-tools-server \
    MCP_PORT=8080 \
    MCP_HOST=0.0.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${MCP_PORT}/health || exit 1

# Expose port
EXPOSE 8080

# Default command
CMD ["python", "servers/production_server.py"]
