# Infrastructure Support for Kailash SDK Development

This directory contains Docker-based infrastructure for advanced Kailash SDK development with databases, message queues, and other services.

## 🚀 Quick Start

### With Docker (Recommended)

```bash
# Start all services
./scripts/start-sdk-dev.sh

# Check status
./scripts/sdk-dev-status.sh

# Stop all services
./scripts/stop-sdk-dev.sh

# Reset everything (WARNING: deletes all data)
./scripts/reset-sdk-dev.sh
```

### Without Docker

See the SDK documentation: `sdk-users/INFRASTRUCTURE_NO_DOCKER.md`

## 📦 What's Included

### Services
- **PostgreSQL**: Main database for workflow storage
- **MongoDB**: Document store for unstructured data
- **Redis**: Cache and message broker
- **Mock API Server**: Testing external integrations
- **MCP Server**: Model Context Protocol support
- **Nginx**: Reverse proxy for services

### Default Ports
- PostgreSQL: 5432
- MongoDB: 27017
- Redis: 6379
- Mock API: 3456
- MCP Server: 3457
- Nginx: 8080

### Credentials
Default credentials (for development only):
- PostgreSQL: `postgres/postgres`
- MongoDB: `admin/admin`
- Redis: No authentication

## 🔧 Configuration

### Environment Variables
Create a `.env` file in your project root:
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=kailash_dev

# MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USER=admin
MONGO_PASSWORD=admin

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Docker Compose Override
For custom configurations, create `docker-compose.override.yml`:
```yaml
version: '3.8'
services:
  postgres:
    ports:
      - "5433:5432"  # Use different port
```

## 📚 Usage Examples

### With PostgreSQL Storage
```python
from kailash.storage.postgres import PostgreSQLStorage

storage = PostgreSQLStorage(
    host="localhost",
    port=5432,
    database="kailash_dev",
    user="postgres",
    password="postgres"
)
```

### With MongoDB
```python
from kailash.nodes.data import MongoDBReaderNode

mongo_reader = MongoDBReaderNode(
    name="mongo_reader",
    connection_string="mongodb://admin:admin@localhost:27017",
    database="workflow_data",
    collection="documents"
)
```

### With Redis Cache
```python
from kailash.cache import RedisCache

cache = RedisCache(
    host="localhost",
    port=6379
)
```

## 🛠️ Troubleshooting

### Common Issues

1. **Ports already in use**
   ```bash
   # Check what's using the port
   lsof -i :5432

   # Or use different ports in docker-compose.override.yml
   ```

2. **Docker not running**
   ```bash
   # Start Docker Desktop or Docker daemon
   docker info
   ```

3. **Permission issues**
   ```bash
   # Make scripts executable
   chmod +x scripts/*.sh
   ```

4. **Services not starting**
   ```bash
   # Check logs
   docker-compose -f docker/docker-compose.sdk-dev.yml logs [service_name]
   ```

### Reset Everything
If things go wrong:
```bash
./scripts/reset-sdk-dev.sh
# This will:
# - Stop all containers
# - Remove all volumes
# - Delete all data
# - Clean up networks
```

## 🔐 Security Notes

⚠️ **Development Only**: These configurations are for development only. Never use default credentials in production.

For production deployments:
- Change all default passwords
- Use environment-specific configurations
- Enable SSL/TLS
- Configure proper authentication
- Set up network isolation

## 📖 Learn More

- [Infrastructure Guide](../sdk-users/INFRASTRUCTURE_GUIDE.md) - Detailed patterns and examples
- [No-Docker Setup](../sdk-users/INFRASTRUCTURE_NO_DOCKER.md) - Manual installation guide
- [Workflow Examples](../sdk-users/workflows/by-pattern/infrastructure/) - Infrastructure-based workflow patterns

## 🤝 Contributing

When adding new infrastructure:
1. Update docker-compose.sdk-dev.yml
2. Add setup instructions here
3. Create example workflows
4. Update relevant documentation
5. Test with clean install

---

*This infrastructure is designed for local development. For production deployments, consult your DevOps team and follow enterprise security guidelines.*
