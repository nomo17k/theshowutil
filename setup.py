#!/usr/bin/env python2.7
"""
MLB the Show Player Rating Utility
"""
import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='theshowutil',
      version='0.1.0',
      author='Taro Sato',
      author_email='okomestudio@gmail.com',
      url='https://github.com/nomo17k/theshowutil',
      description='MLB the Show player rating utility',
      long_description=read('README'),
      license='BSD',
      packages=['theshowutil'],
      package_dir={'theshowutil': 'theshowutil'},
      scripts=['bin/theshowrater',
               'bin/theshowfinder'],
      classifiers=["Development Status :: 3 - Alpha"]
      )
