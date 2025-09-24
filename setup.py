# setup.py
from setuptools import setup, find_packages

setup(
    name="ai-content-factory",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "flask>=2.0.0",
        "requests>=2.25.0",
        "psycopg2-binary>=2.8.6",
        "python-dotenv>=0.19.0",
        "pytrends>=4.8.0",
        "google-api-python-client>=2.0.0",
        "sqlalchemy>=1.4.0",
        "jinja2>=3.0.0",
    ],
    python_requires=">=3.8",
    author="Your Name",
    description="AI-powered content creation factory using Groq",
    package_dir={"": "."},
)