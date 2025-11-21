from setuptools import setup, find_packages

setup(
    name="explore_agent",
    version="0.1.0",
    description="Autonomous codebase exploration agent with plan-execute-synthesize loop",
    author="Phoenix System",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[
        # Core dependencies
        "typing-extensions>=4.0",
        # LLM provider interface (needs to be provided externally)
        # Optional: Can be installed separately
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
