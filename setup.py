#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()


requirements = [
    "rdflib>=6,<7",
    "lxml>=4.2,<5",
    "python-slugify>=5,<8",
]


setup(
    author="Peter Andorfer",
    author_email="peter.andorfer@oeaw.ac.at",
    python_requires=">=3.8",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
    ],
    description="Helper functions for the generation of CIDOC CRMish RDF",
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    name="acdh_cidoc_pyutils",
    packages=find_packages(include=["acdh_cidoc_pyutils", "acdh_cidoc_pyutils.*"]),
    setup_requires=[],
    test_suite="tests",
    tests_require=[],
    url="https://github.com/acdh-oeaw/acdh-cidoc-pyutils",
    version="v0.5",
    zip_safe=False,
)
