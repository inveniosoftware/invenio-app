# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
# Copyright (C) 2021      TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""WSGI, Celery and CLI applications for Invenio flavours."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'pytest-invenio>=1.4.2',
    'redis>=2.10.5',
]

extras_require = {
    'docs': [
        'Sphinx==4.2.0',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)


install_requires = [
    'flask-celeryext>=0.3.4',
    'flask-limiter>=1.0.1,<1.2.0',
    'limits>=1.5.1,<2.0',
    'flask-shell-ipython>=0.3.1',
    'flask-talisman>=0.3.2,<1.0',
    'invenio-base>=1.2.3',
    'invenio-cache>=1.0.0',
    'invenio-config>=1.0.0',
    'uritools>=1.0.1',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_app', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-app',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio applications',
    license='MIT',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-app',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'console_scripts': [
            'invenio = invenio_app.cli:cli',
        ],
        'invenio_base.api_apps': [
            'invenio_app = invenio_app:InvenioApp',
        ],
        'invenio_base.apps': [
            'invenio_app = invenio_app:InvenioApp',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Development Status :: 5 - Production/Stable',
    ],
)
