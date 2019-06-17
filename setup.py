#!/usr/bin/env python

from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

setup(
    name="pybuses-entities",
    version="0.0.1",
    description="Data classes to work with Stops and Buses/vehicles on a public transportation network",
    author="David Lorenzo",
    url="https://github.com/David-Lor/PyBuses",
    packages=("pybusent",),
    install_requires=("pydantic",),
    license="Apache 2.0",
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ),
    long_description_content_type="text/markdown",
    long_description=long_description,
)
