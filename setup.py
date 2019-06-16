#!/usr/bin/env python

from setuptools import setup

setup(
    name="pybuses-entities",
    version="0.1.0",
    description="Data classes to work with Stops and Buses/vehicles on a public transportation network",
    long_description="The goal of PyBusEnt is to provide a set of data classes that help organizing, managing and "
                     "working with the Stops and Buses on a public transportation network backend or frontend "
                     "Python project. This project was mainly focused on a Telegram Bot backend and an API to provide "
                     "all the data required (Stops and Buses coming to these stops).",
    author="David Lorenzo",
    url="https://github.com/David-Lor/PyBuses",
    packages=("pybuses_entities",),
    install_requires=("pydantic",),
    # test_suite="tests.run_all_tests"
)
