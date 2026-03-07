#!/usr/bin/env python
"""Setup script for CascConf.

This is a minimal setup.py that delegates to pbr for configuration.
All project metadata is defined in setup.cfg and pyproject.toml.
"""

from setuptools import setup

setup(
    setup_requires=['pbr>=5.0'],
    pbr=True,
)
