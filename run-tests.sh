#!/usr/bin/env sh
# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# Quit on errors
set -o errexit

# Quit on unbound symbols
set -o nounset

export PYTEST_ADDOPTS='docs tests invenio_app'

pydocstyle invenio_app tests docs
isort invenio_app tests --check-only --diff
check-manifest --ignore ".*-requirements.txt"
sphinx-build -qnNW docs docs/_build/html
python setup.py test
