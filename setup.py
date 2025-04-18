from setuptools import setup, find_packages

setup(
    name="parser",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "transformers>=4.36.2",
        "torch>=2.1.0",
        "numpy>=1.26.0",
        "pandas>=2.1.4",
        "scikit-learn>=1.3.2",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "aiohttp>=3.9.1",
    ],
) 