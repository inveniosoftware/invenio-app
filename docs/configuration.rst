..
    This file is part of Invenio.
    Copyright (C) 2017 CERN.

    Invenio is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, CERN does not
    waive the privileges and immunities granted to it by virtue of its status
    as an Intergovernmental Organization or submit itself to any jurisdiction.


Configuration
=============

You can modify the default location of the instance folder and/or static folder
by setting the environment variables:

- ``INVENIO_INSTANCE_PATH`` (default: ``<sys.prefix>/var/instance/``)

- ``INVENIO_STATIC_FOLDER``  (default: ``<instance-path>/static/``)

Instance specific configuration is loaded from:

- ``<instance-path>/invenio.cfg``
- via environment variables prefixed with ``INVENIO_`` (e.g.
  ``INVENIO_SQLALCHEMY_DATABASE_URI``)

Templates are loaded from:

- ``<instance-path>/templates/``

.. automodule:: invenio_app.config
   :members:
