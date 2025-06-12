"""Setup script for MIDT Python Pipeline."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "MIDT fMRI Analysis Pipeline - Python Edition"

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
with open(requirements_file, "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="midt-pipeline",
    version="2.0.0",
    author="MIDT Pipeline Team",
    author_email="uqahonne@uq.edu.au",
    description="A comprehensive Python pipeline for analyzing Monetary Incentive Delay Task (MIDT) fMRI data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/midt-python-pipeline",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "midt-pipeline=midt_pipeline.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "midt_pipeline": ["examples/*.yaml", "examples/*.json"],
    },
    keywords="fMRI neuroimaging MIDT nilearn BIDS",
    project_urls={
        "Bug Reports": "https://github.com/your-username/midt-python-pipeline/issues",
        "Source": "https://github.com/your-username/midt-python-pipeline",
        "Documentation": "https://midt-python-pipeline.readthedocs.io/",
    },
)