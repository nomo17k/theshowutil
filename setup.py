#!/usr/bin/env python2.7
"""
MLB the Show Player Rating Utility
"""
from distutils.core import setup


__version__ = '2012109'
__author__ = 'Taro Sato'
__author_email__ = 'okomestudio@gmail.com'


def make_descriptions(docstr=__doc__):
    """
    Make __doc__ into short and long package descriptions.
    """
    docstrs = docstr.strip().split("\n")
    description = docstrs[0].strip()
    long_description = "\n".join(docstrs[2:])
    return description, long_description


def main():
    descr_short, descr_long = make_descriptions()

    scripts = ['bin/theshowrater',
               'bin/theshowfinder']

    setup(name='theshowutil',
          version=__version__,
          author=__author__,
          author_email=__author_email__,
          maintainer=__author__,
          maintainer_email=__author_email__,
          url='',
          description=descr_short,
          long_description=descr_long,
          download_url='',
          platforms=['Linux'],
          license='GPL',
          packages=['theshowutil'],
          package_dir={'theshowutil': 'theshowutil'},
          scripts=scripts,
          ext_modules=[])


if __name__ == "__main__":
    main()
