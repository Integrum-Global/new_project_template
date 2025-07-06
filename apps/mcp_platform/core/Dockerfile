# Multi-stage Dockerfile for MCP Application

# Build stage
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 mcpuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/mcpuser/.local

# Copy application code
COPY --chown=mcpuser:mcpuser . .

# Install the application
RUN pip install -e .

# Set environment variables
ENV PATH=/home/mcpuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

# Create directories for data
RUN mkdir -p /app/data /app/logs && \
    chown -R mcpuser:mcpuser /app/data /app/logs

# Switch to app user
USER mcpuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "apps.mcp.main"]
