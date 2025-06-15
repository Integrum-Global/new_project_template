"""
Test Suite for Docker Infrastructure Support

This test suite ensures that:
1. Studio can launch with Docker infrastructure
2. All required services are available
3. Database connections work correctly
4. Infrastructure is properly configured
"""

import asyncio
import os
import subprocess
import time
from pathlib import Path

import pytest
import requests


class TestDockerInfrastructure:
    """Test Docker infrastructure for Studio."""

    @pytest.fixture(scope="class")
    def docker_services(self):
        """Start Docker services for testing."""
        # Use the unified docker-compose.yml
        compose_file = Path(
            "/Users/esperie/repos/projects/kailash_python_sdk/docker/docker-compose.yml"
        )

        if not compose_file.exists():
            pytest.skip("Docker compose file not found")

        # Start services
        subprocess.run(
            ["docker-compose", "-f", str(compose_file), "up", "-d"],
            check=True,
            cwd=compose_file.parent,
        )

        # Wait for services to be ready
        time.sleep(30)

        yield

        # Cleanup
        subprocess.run(
            ["docker-compose", "-f", str(compose_file), "down"], cwd=compose_file.parent
        )

    def test_postgresql_service(self, docker_services):
        """Test PostgreSQL database service is running."""
        import psycopg2

        try:
            # Test connection to PostgreSQL with pgvector
            conn = psycopg2.connect(
                host="localhost",
                port=5433,
                database="kailash",
                user="kailash",
                password="kailash123",
            )

            # Test that pgvector extension is available
            cursor = conn.cursor()
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            result = cursor.fetchone()

            assert result[0] == "vector", "pgvector extension not installed"

            conn.close()

        except Exception as e:
            pytest.fail(f"PostgreSQL connection failed: {e}")

    def test_redis_service(self, docker_services):
        """Test Redis service is running."""
        import redis

        try:
            r = redis.Redis(host="localhost", port=6379, decode_responses=True)
            r.ping()
            r.set("test_key", "test_value")
            assert r.get("test_key") == "test_value"
            r.delete("test_key")

        except Exception as e:
            pytest.fail(f"Redis connection failed: {e}")

    def test_qdrant_service(self, docker_services):
        """Test Qdrant vector database service is running."""
        try:
            response = requests.get("http://localhost:6333/")
            assert response.status_code == 200

            # Test collection creation
            response = requests.put(
                "http://localhost:6333/collections/test_collection",
                json={"vectors": {"size": 100, "distance": "Cosine"}},
            )
            assert response.status_code in [200, 409]  # 409 if already exists

        except Exception as e:
            pytest.fail(f"Qdrant connection failed: {e}")

    def test_ollama_service(self, docker_services):
        """Test Ollama LLM service is running."""
        try:
            response = requests.get("http://localhost:11434/api/tags")
            assert response.status_code == 200

        except Exception as e:
            pytest.fail(f"Ollama connection failed: {e}")

    def test_studio_with_docker_infrastructure(self, docker_services):
        """Test Studio can connect to Docker infrastructure."""
        # Set environment variables for Docker services
        os.environ.update(
            {
                "STUDIO_DATABASE_URL": "postgresql://kailash:kailash123@localhost:5433/kailash",
                "REDIS_URL": "redis://localhost:6379",
                "QDRANT_URL": "http://localhost:6333",
                "OLLAMA_BASE_URL": "http://localhost:11434",
                "STUDIO_ENVIRONMENT": "testing",
            }
        )

        # Import and test Studio components
        try:
            from apps.studio.api.main import create_studio_gateway
            from apps.studio.core.config import get_config

            config = get_config()

            # Verify config picks up Docker URLs
            assert "localhost:5433" in config.get_database_url()

            # Test gateway creation (this will test middleware connectivity)
            gateway = create_studio_gateway()

            # Verify gateway components
            assert hasattr(gateway, "app")
            assert hasattr(gateway, "agent_ui")
            assert hasattr(gateway, "realtime")
            assert hasattr(gateway, "schema_registry")
            assert hasattr(gateway, "node_registry")

            # Test that middleware components are SDK-based
            assert gateway.agent_ui.__class__.__module__.startswith("kailash.")
            assert gateway.realtime.__class__.__module__.startswith("kailash.")

        except Exception as e:
            pytest.fail(
                f"Studio gateway creation with Docker infrastructure failed: {e}"
            )

    def test_studio_endpoints_with_docker(self, docker_services):
        """Test Studio endpoints work with Docker infrastructure."""
        # This test would require actually starting the Studio server
        # For now, we'll test component initialization

        os.environ.update(
            {
                "STUDIO_DATABASE_URL": "postgresql://kailash:kailash123@localhost:5433/kailash",
                "STUDIO_ENVIRONMENT": "testing",
                "STUDIO_ENABLE_AUTH": "false",  # Disable auth for testing
            }
        )

        try:
            from apps.studio.api.main import create_studio_gateway
            from apps.studio.api.routes import add_studio_routes

            # Create gateway with Docker infrastructure
            gateway = create_studio_gateway()

            # Add Studio routes
            add_studio_routes(gateway)

            # Verify routes were added
            route_paths = [route.path for route in gateway.app.routes]

            # Check PRD-required endpoints exist
            assert "/api/chat" in route_paths
            assert "/api/workflows/{workflow_id}/export" in route_paths
            assert "/api/nodes/types" in route_paths
            assert "/api/workflows/{workflow_id}/live" in route_paths

        except Exception as e:
            pytest.fail(f"Studio routes setup with Docker infrastructure failed: {e}")

    def test_all_infrastructure_ready(self, docker_services):
        """Test all required infrastructure services are ready."""
        services = {
            "PostgreSQL": ("localhost", 5433),
            "Redis": ("localhost", 6379),
            "Qdrant": ("localhost", 6333),
            "Ollama": ("localhost", 11434),
        }

        for service_name, (host, port) in services.items():
            try:
                import socket

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()

                assert (
                    result == 0
                ), f"{service_name} service not available on {host}:{port}"

            except Exception as e:
                pytest.fail(f"Failed to check {service_name} service: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
