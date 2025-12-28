#!/usr/bin/env python3
"""
K3NG Rotator Configuration & Testing Utility
Setup Script
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith('#')
        ]
else:
    requirements = [
        'PyQt6>=6.6.0',
        'pyserial>=3.5',
        'Jinja2>=3.1.2',
        'pycparser>=2.21',
        'jsonschema>=4.17.0',
        'markdown>=3.5.0',
        'matplotlib>=3.8.0',
        'numpy>=1.26.0',
        'pyyaml>=6.0.1',
        'python-dotenv>=1.0.0',
    ]

setup(
    name="k3ng-config-tool",
    version="0.4.0",
    author="K3NG Project Contributors",
    author_email="",
    description="Configuration and testing utility for K3NG rotator controllers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/k3ng/k3ng_rotator_controller",
    packages=find_packages(exclude=['tests', 'tests.*']),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications :: Ham Radio",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-qt>=4.2.0',
            'pytest-cov>=4.1.0',
            'mypy>=1.7.0',
            'types-PyYAML>=6.0.12',
        ],
    },
    entry_points={
        'console_scripts': [
            'k3ng-config=main:main',
        ],
        'gui_scripts': [
            'k3ng-config-gui=gui_main:main',
        ],
    },
    include_package_data=True,
    package_data={
        'k3ng_config_tool': [
            'data/board_definitions/*.json',
            'data/validation_rules/*.yaml',
            'generators/templates/*.j2',
        ],
    },
    zip_safe=False,
)
