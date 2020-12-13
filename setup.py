#  This file is part of easygdf and is released under the BSD 3-clause license

from setuptools import setup

setup(
    name='easygdf',
    version='2.0',
    description='A python library to make working with GDF files a breeze.',
    author='Christopher M. Pierce',
    author_email='contact@chris-pierce.com',
    packages=['easygdf', 'easygdf.tests'],
    package_data={'easygdf': ['data/*'], 'easygdf.tests': ['data/*']},
    include_package_data=True,
    install_requires=['numpy'],
    classifiers=[
        "License :: OSI Approved :: BSD License",
    ],
    python_requires='>=3.6',
    liense="BSD",
)
