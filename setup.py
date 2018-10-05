# -*- coding: utf-8 -*-
# imports - standard imports
from setuptools import setup, find_packages
import re
import ast

# get version from __version__ variable in frappe/__init__.py
_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('requirements.txt') as f:
    install_requires = f.read().strip().split('\n')

with open('frappe_s3_attachment/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='frappe_s3_attachment',
    version=version,
    description='Frappe app to make file upload to S3 through attach file option.',
    author='Frappe',
    author_email='ramesh.ravi@zerodha.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
    dependency_links=[]
)
