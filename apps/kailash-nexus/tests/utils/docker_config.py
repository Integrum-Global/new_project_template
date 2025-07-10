# Docker infrastructure configuration for Nexus tests
# Based on the main tests/utils/docker_config.py
import os

# PostgreSQL configuration - using Docker container on port 5434
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5434")),
    "database": os.getenv("DB_NAME", "kailash_test"),
    "user": os.getenv("DB_USER", "test_user"),
    "password": os.getenv("DB_PASSWORD", "test_password"),
}

# Redis configuration - using test Redis on port 6380
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6380")),
}

# MySQL configuration - using test MySQL on port 3307
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3307")),
    "database": os.getenv("MYSQL_DATABASE", "kailash_test"),
    "user": os.getenv("MYSQL_USER", "kailash_test"),
    "password": os.getenv("MYSQL_PASSWORD", "test_password"),
}


# Connection string helpers
def get_postgres_connection_string(database=None):
    """Get PostgreSQL connection string for the Docker setup."""
    db = database or DATABASE_CONFIG["database"]
    return (
        f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
        f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{db}"
    )


def get_redis_connection_params():
    """Get Redis connection parameters for direct client setup."""
    return REDIS_CONFIG


def get_mysql_connection_string(database=None):
    """Get MySQL connection string for the Docker setup."""
    db = database or MYSQL_CONFIG["database"]
    return (
        f"mysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}"
        f"@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{db}"
    )


async def ensure_docker_services():
    """Ensure Docker services are available."""
    import asyncio

    try:
        # Check PostgreSQL
        import asyncpg

        conn = await asyncpg.connect(get_postgres_connection_string())
        await conn.close()

        # Check Redis
        import redis

        r = redis.Redis(**REDIS_CONFIG)
        r.ping()

        # Check MySQL
        import pymysql

        conn = pymysql.connect(
            host=MYSQL_CONFIG["host"],
            port=MYSQL_CONFIG["port"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
            database=MYSQL_CONFIG["database"],
        )
        conn.close()

        return True
    except Exception as e:
        print(f"Docker services check failed: {e}")
        return False
