#
# Upload to pypi:
#   python setup.py sdist bdist_wheel
#   twine upload dist/*
#
#   To use these commands install wheel and twine
#   pip install wheel twine
#
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import os
import io
import itertools
import re
import ast

_version_re = re.compile(r'__version__\s+=\s+(.*)')
_license_re = re.compile(r'__license__\s+=\s+(.*)')
_author_re = re.compile(r'__author__\s+=\s+(.*)')
line_numbers = 20

with io.open('femagtools/__init__.py', 'r') as f:
    meta_data = list(itertools.islice(f, line_numbers))
meta_data = ''.join(meta_data)

version = str(ast.literal_eval(_version_re.search(meta_data).group(1)))
license = str(ast.literal_eval(_license_re.search(meta_data).group(1)))
author = str(ast.literal_eval(_author_re.search(meta_data).group(1)))

here = os.path.abspath(os.path.dirname(__file__))
# Get the long description from the README file
with io.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    description='Python API for FEMAG',
    long_description=long_description,
    author=author,
    url='https://github.com/SEMAFORInformatik/femagtools',
    author_email='tar@semafor.ch',
    version=version,
    platforms="any",
    install_requires=['numpy', 'scipy>=1.7', 'mako', 'six', 'lmfit',
                      'dxfgrabber', 'networkx', 'netCDF4'],
    extras_require={"meshio": ["meshio", "lxml"]},
    packages=['femagtools', 'femagtools.moo', 'femagtools.dxfsl'],
    package_data={'femagtools': ['templates/*.mako']},
    license=license,
    name='femagtools',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering'],
    entry_points={"console_scripts": [
        "femagtools-plot = femagtools.plot:main",
        "femagtools-convert = femagtools.convert:main",
        "femagtools-bchxml = femagtools.bchxml:main",
        "femagtools-dxfsl = femagtools.dxfsl.conv:main"]}
)
