from setuptools import setup, find_packages

setup(
    name="data_analyzer",
    version="0.1.3",
    packages=find_packages(),
    install_requires=[
        "pandas",
        # other dependencies if necessary
    ],
    author="Mohamad",
    description="A library to validate and scan the QEVD dataset structure.",
)
