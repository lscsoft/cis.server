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

import os
import datetime

import django.db
from django.core.management.base import BaseCommand

from reversion import revisions as reversion

from ... import version
from .. import functions
from .. models import UpdateInfo

__version__ = version.version
__author__ = 'Brian Moe, Duncan.macleod <duncan.macleod@ligo.org>'
__credits__ = 'The LIGO Scientific Collaboration, The LIGO Laboratory'


class Command(BaseCommand):
    """Update the CIS database by parsing INI files in one or more directories
    """
    help = __doc__.rstrip('\n ')

    def add_arguments(self, parser):
        """Add arguments to the command-line parser

        This function is only used for Django >= 1.8
        """
        parser.add_argument('updateId')
        parser.add_argument('ifo')
        parser.add_argument('directory', nargs='+',
                            help="Location of model files")

    def handle(self, updateId, ifo, directory=[], **kwargs):
        """Update the CIS database from DAQ INI files in the given directories
        """
        updateId = int(updateId)
        if ifo.lower() in ['virgo', 'v1']:
            update_model = functions.update_virgo_model
        else:
            update_model = functions.update_ligo_model
        if isinstance(directory, str):
            directory = directory.split(',')
        for d in directory:
            for fname in os.listdir(d):
                source = os.path.splitext(os.path.basename(fname))[0]
                path = os.path.join(d, fname)
                if not (source.startswith(ifo) and fname.endswith('ini')):
                    continue
                with reversion.create_revision():
                    reversion.add_meta(
                        UpdateInfo, ifo=ifo, model=source, updateId=updateId,
                        date=datetime.datetime.now())
                    update_model(path, source,
                                 verbose=kwargs.get('verbose', 1))
                django.db.reset_queries()
