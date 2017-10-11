#!/usr/bin/env python3

from setuptools import setup


setup(
    name='listener',

    version='1.0.0.dev1',

    description='Utility for listener component of Green-Box of HCA-DCP',

    url='https://github.com/HumanCellAtlas/secondary-analysis',

    author='Rex Wang',
    author_email='chengche@broadinstitute.org',

    license='BSD 3-clause "New" or "Revised" License',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',

        'Intended Audience :: Developers',

        'Topic :: Scientific/Engineering :: Bio-Informatics',

        'Programming Language :: Python :: 3 :: Only',
    ],

    packages=['listener', 'tests'],

    # Prequisite packages
    install_requires=[],

    # Commandline entry points
    entry_points={

    }
)