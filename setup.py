from setuptools import setup, find_packages

setup(
    name="protein_site_explainer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "pytest",
        "requests",
        "pandas",
        "numpy",
        "plotly",
        "py3Dmol",
        "biopython",
        "scikit-learn",
        "torch",
        "esm",
        "joblib",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="Protein site mutation explorer with ESM scoring",
    license="MIT",
    keywords="protein mutation ESM AlphaFold UniProt",
)
