#!/usr/bin/env python3
"""
Setup script for X12 EDI Converter package

This file exists for backwards compatibility with older pip versions.
Configuration is primarily in pyproject.toml.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README for the long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8") if (this_directory / "README.md").exists() else ""

# Read version from package
version = "1.0.0"
try:
    with open("x12_edi_converter/__init__.py", "r") as f:
        for line in f:
            if line.startswith("__version__"):
                version = line.split("=")[1].strip().strip('"').strip("'")
                break
except FileNotFoundError:
    pass

setup(
    name="pyedi",
    version=version,
    author="James",
    author_email="",
    description="A comprehensive Python package for parsing, transforming, and mapping X12 EDI files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jaymd96/pyedi",
    packages=find_packages(exclude=["tests*", "docs*", "examples*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup",
        "Topic :: Office/Business :: Financial",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyx12>=2.3.3",
        "jsonata>=0.2.0",
    ],
    extras_require={
        "cli": [
            "click>=8.0",
            "colorama>=0.4.4",
        ],
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=22.0",
            "flake8>=5.0",
            "mypy>=1.0",
            "pre-commit>=3.0",
        ],
        "docs": [
            "sphinx>=5.0",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "x12-convert=x12_edi_converter.cli.main:main",
        ],
    },
    package_data={
        "x12_edi_converter": ["examples/sample_mappings/*.json"],
    },
    include_package_data=True,
    zip_safe=False,
)