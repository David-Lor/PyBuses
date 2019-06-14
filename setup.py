#!/usr/bin/env python

from setuptools import setup

setup(
    name="PyBuses",
    version="0.1.0",
    description="Python framework to help organizing and working with Buses and Stops",
    long_description="PyBuses is a Python framework intended to help organizing and working with Buses and Stops "
                     "on a server-based app that serves information about a public transportation service to users. "
                     "The working principle is searching stops and getting the buses that will arrive to a certain "
                     "stop in real-time, with the remaining time until arrival. "
                     "The framework is based on the usage of functions that retrieve all the required information "
                     "from online sources (like APIs) or offline sources (like databases or caches).",
    author="David Lorenzo",
    url="https://github.com/David-Lor/PyBuses",
    packages=("pybuses",),
    install_requires=("pymongo", "requests",),
    test_suite="tests.run_all_tests"
)
