from setuptools import setup, find_packages

setup(
    name="ai-chat-backend",
    version="0.1.0",
    description="AI Chat Backend API using FastAPI and Ollama",
    author="AI Chat Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "ollama>=0.1.7",
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        "python-multipart>=0.0.6",
        "python-json-logger>=2.0.0",
        "aiosqlite>=0.19.0",
        "pymysql>=1.1.0",
        "pandas>=2.0.0",
        "fastapi-cors>=0.0.6",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "httpx>=0.25.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ai-chat-backend=backend.main:main",
        ],
    },
)
