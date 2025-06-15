"""
Setup configuration for Kailash Studio API
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="kailash-studio-api",
    version="1.0.0",
    description="Comprehensive REST API for the Kailash Workflow Studio",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Kailash SDK Team",
    author_email="team@kailash-sdk.com",
    url="https://github.com/kailash-sdk/kailash-python-sdk",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # Core Kailash SDK
        "kailash-sdk>=1.0.0",
        # FastAPI and async support
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "websockets>=12.0",
        "pydantic>=2.0.0",
        # Database and async operations
        "aiosqlite>=0.19.0",
        "asyncpg>=0.29.0",  # For PostgreSQL support
        # CLI interface
        "click>=8.0.0",
        "rich>=13.0.0",  # For beautiful CLI output
        # Authentication and security
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.6",
        # Data processing
        "pyyaml>=6.0",
        "orjson>=3.9.0",  # Fast JSON processing
        # HTTP client
        "httpx>=0.25.0",
        # Logging and monitoring
        "structlog>=23.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "production": [
            "gunicorn>=21.0.0",
            "prometheus-client>=0.17.0",
            "sentry-sdk[fastapi]>=1.32.0",
        ],
        "postgresql": [
            "asyncpg>=0.29.0",
            "psycopg2-binary>=2.9.0",
        ],
        "testing": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.25.0",
            "factory-boy>=3.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "studio=apps.studio.cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: FastAPI",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords=[
        "workflow",
        "automation",
        "api",
        "fastapi",
        "websocket",
        "ai",
        "llm",
        "real-time",
        "enterprise",
        "kailash",
    ],
    project_urls={
        "Documentation": "https://github.com/kailash-sdk/kailash-python-sdk/tree/main/apps/studio",
        "Source": "https://github.com/kailash-sdk/kailash-python-sdk",
        "Tracker": "https://github.com/kailash-sdk/kailash-python-sdk/issues",
    },
    include_package_data=True,
    zip_safe=False,
)
