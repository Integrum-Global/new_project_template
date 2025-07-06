"""
MCP Application Setup
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-management-system",
    version="1.0.0",
    author="Kailash SDK Team",
    author_email="team@kailash.dev",
    description="Enterprise-grade Model Context Protocol management system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kailash/mcp-app",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "kailash-sdk>=0.6.0",
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.23.0",
        "pydantic>=2.0.0",
        "aiohttp>=3.8.0",
        "websockets>=11.0",
        "redis>=4.5.0",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "pyyaml>=6.0",
        "python-jose[cryptography]>=3.3.0",
        "bcrypt>=4.0.0",
        "pyotp>=2.8.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.3.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.3.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "sphinx-autodoc-typehints>=1.23.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mcp-app=apps.mcp.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "apps.mcp": [
            "config/*.yaml",
            "config/*.yml",
            "templates/*.html",
            "static/**/*",
        ],
    },
)
