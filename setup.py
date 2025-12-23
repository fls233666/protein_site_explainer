from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="protein_site_explainer",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "streamlit>=1.20.0",
        "requests>=2.31.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "plotly>=5.15.0",
        "py3Dmol==2.0.0.post2",
        "stmol>=1.0.0",
        "biopython>=1.81",
        "scikit-learn>=1.3.0",
        "torch>=2.0.0",
        "esm>=2.0.0",
        "joblib>=1.3.0",
        "kaleido>=0.2.0",
    ],
    extras_require={
        "cpu": [
            "torch>=2.0.0+cpu",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Protein site mutation explorer with ESM scoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    keywords="protein mutation ESM AlphaFold UniProt",
    entry_points={
        "console_scripts": [
            "protein_site_explainer=app:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    python_requires=">=3.9",
)
