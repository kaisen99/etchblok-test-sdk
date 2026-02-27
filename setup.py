from setuptools import setup, find_packages

setup(
    name="eventkit",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=["typing_extensions>=4.0"],
    description="Lightweight event bus with middleware and pluggable storage",
)
