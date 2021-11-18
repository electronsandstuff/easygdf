#  This file is part of easygdf and is released under the BSD 3-clause license

from setuptools import setup

setup(
    name='easygdf',
    version='2.0.7',
    description='A python library to make working with GDF files a breeze.',
    long_description='A python library to make working with GDF files a breeze.  Check out our project on [github](https://github.com/electronsandstuff/easygdf)!',
    long_description_content_type='text/markdown',
    author='Christopher M. Pierce',
    author_email='contact@chris-pierce.com',
    packages=['easygdf', 'easygdf.tests'],
    package_data={'easygdf': ['data/*'], 'easygdf.tests': ['data/*']},
    include_package_data=True,
    install_requires=['numpy'],
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires='>=3.6',
    license="BSD-3-Clause",
)
