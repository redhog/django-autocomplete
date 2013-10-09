#! /usr/bin/python

from setuptools.command import easy_install
from setuptools import setup, find_packages
import shutil
import os.path
import sys
import hashlib

PKG_DIR = os.path.abspath(os.path.dirname(__file__))
PKG_NAME = os.path.basename(PKG_DIR)

# Make it possible to overide script wrapping
old_is_python_script = easy_install.is_python_script
def is_python_script(script_text, filename):
    if 'SETUPTOOLS_DO_NOT_WRAP' in script_text:
        return False
    return old_is_python_script(script_text, filename)
easy_install.is_python_script = is_python_script

setup(
    name = "django_autocomplete_foreignkey",
    description = "AutoComplete for ForeignKey and ManyToManyField.",
    keywords = "django autocomplete foreignkey",
    install_requires = [],
    version = "0.0.1",
    author = "nikolovski.darko@gmail.com",
    author_email = "nikolovski.darko@gmail.com",
    license = "GPL",
    url = "https://github.com/redhog/django-autocomplete",
    packages = find_packages(),
    package_data = {'': ['*.txt', '*.css', '*.html', '*.js']},
    include_package_data = True
)
