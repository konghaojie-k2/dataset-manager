#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup configuration for dm CLI
"""

from setuptools import setup, find_packages

setup(
    name="dm",
    version="0.1.0",
    description="Dataset Manager CLI - AI-Native data management tool",
    author="AI Assistant",
    py_modules=["dm_cli"],
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
    ],
    entry_points={
        "console_scripts": [
            "dm=dm_cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: 3.11",
    ],
)
