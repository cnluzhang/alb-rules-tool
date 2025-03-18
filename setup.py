"""Setup script for the ALB Rules Tool."""

from setuptools import setup, find_packages

setup(
    name="alb-rules-tool",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "boto3>=1.26.0",
        "click>=8.1.3",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "alb-rules=alb_rules_tool.cli:cli",
        ],
    },
    python_requires=">=3.8",
    author="AWS Administrator",
    author_email="your-email@example.com",
    description="AWS ALB Rules backup and restore tool",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Systems Administration",
    ],
)