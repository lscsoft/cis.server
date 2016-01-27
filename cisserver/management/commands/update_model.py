# -*- coding: utf-8 -*-
# Copyright (C) Brian Moe (2013-2014), Duncan Macleod (2014-)
#
# This file is part of LIGO CIS Core.
#
# LIGO CIS Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# LIGO CIS Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with LIGO CIS Core.  If not, see <http://www.gnu.org/licenses/>.

"""Update the CIS database by parsing an INI file from a DAQ model
"""

import os
import datetime

import reversion
import django.db
from django import get_version
from django.core.management.base import BaseCommand

from ..models import UpdateInfo
from ..functions import (update_ligo_model, update_virgo_model)
from ... import version

__version__ = version.version
__author__ = 'Brian Moe, Duncan.macleod <duncan.macleod@ligo.org>'
__credits__ = 'The LIGO Scientific Collaboration, The LIGO Laboratory'

DJANGO_VERSION = get_version()


class Command(BaseCommand):
    """Update the CIS database by parsing an INI file from a DAQ model
    """
    args = 'updateId ifo model'
    help = __doc__.rstrip('\n ')

    def add_arguments(self, parser):
        """Add arguments to the command-line parser
        """
        parser.add_argument('updateId', type=int, help='ID for this update')
        parser.add_argument('ifo', help='prefix of IFO for this model')
        parser.add_argument('model', help='name of model to update')
        parser.add_argument('-d', '--directory', default='daq',
                            help='parent directory of model INI files, '
                                 'default: %(default)s')
        return parser

    def handle(self, updateId, ifo, *models, **options):
        """Update channel entries for one or more models
        """
        for model in models:
            fname = os.path.join(options['directory'], model)
            if not fname.endswith(".ini"):
                fname = fname + ".ini"

            updateId = int(updateId)
            source = os.path.splitext(os.path.basename(fname))[0]
            with reversion.create_revision():
                reversion.add_meta(UpdateInfo, ifo=ifo, model=source,
                                   updateId=updateId,
                                   date=datetime.datetime.now())
                if ifo.lower() in ['virgo', 'v1']:
                    update_virgo_model(fname)
                else:
                    update_ligo_model(fname)
            django.db.reset_queries()
