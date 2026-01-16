from setuptools import setup, find_packages

setup(
    name="logix",
    version="0.1.0",
    description="A Python CLI agent that analyzes system logs using LLMs.",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
        "rich>=13.0.0",
        "requests>=2.0.0",
        "psutil>=5.0.0",
    ],
    entry_points={
        "console_scripts": [
            "logix=src.main:main",
        ],
    },
    python_requires=">=3.8",
)
