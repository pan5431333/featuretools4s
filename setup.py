#!/usr/bin/env python
# coding=utf-8

from setuptools import setup, find_packages

setup(
    name='featuretools4s',
    version="0.1.5",
    description=(
        'Run FeatureTools to automate Feature Engineering distributionally on Spark. '
    ),
    long_description=open('README.md').read(),
    author='Meng Pan',
    author_email='meng.pan95@gmail.com',
    maintainer='Meng Pan',
    maintainer_email='meng.pan95@gmail.com',
    license='BSD License',
    packages=find_packages(),
    platforms=["all"],
    url='https://github.com/pan5431333/featuretools4s',
    install_requires=[
        'pyspark>=2.1',
        'numpy>=1.14.5',
        'pandas>=0.23.1',
        'featuretools>=0.3.0'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries'
    ],
)
