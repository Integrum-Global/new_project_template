"""
Setup configuration for QA Agentic Testing application.
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="qa-agentic-testing",
    version="0.1.0",
    description="AI-powered autonomous testing framework using advanced agent systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Kailash SDK Team",
    author_email="team@kailash.dev",
    url="https://github.com/KailashSDK/kailash-python-sdk",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "click>=8.0.0",
        "pydantic>=2.0.0",
        "aiosqlite>=0.19.0",
        "pathlib>=1.0.0",
        "jinja2>=3.1.0",
        "python-multipart>=0.0.6",
        "httpx>=0.25.0",
        "websockets>=11.0.0",
        "kailash",  # Main SDK dependency
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "frontend": [
            "nodejs>=16.0.0",  # For React frontend development
        ],
        "ollama": [
            "ollama>=0.1.0",  # For local LLM support
        ],
        "openai": [
            "openai>=1.0.0",  # For OpenAI GPT support
        ],
        "anthropic": [
            "anthropic>=0.7.0",  # For Claude support
        ],
    },
    entry_points={
        "console_scripts": [
            "qa-test=qa_agentic_testing.cli.main:cli",
            "qa-agentic-testing=qa_agentic_testing.cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Framework :: FastAPI",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="testing qa ai llm agents autonomous framework kailash",
    project_urls={
        "Bug Reports": "https://github.com/KailashSDK/kailash-python-sdk/issues",
        "Source": "https://github.com/KailashSDK/kailash-python-sdk",
        "Documentation": "https://docs.kailash.dev/qa-agentic-testing",
    },
)
