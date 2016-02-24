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

from __future__ import print_function

import os
import datetime

from django.db import reset_queries
from django.core.management.base import BaseCommand

from reversion import revisions as reversion

import ligo.org

from ... import version
from .. import functions

__version__ = version.version
__author__ = 'Brian Moe, Duncan.macleod <duncan.macleod@ligo.org>'
__credits__ = 'The LIGO Scientific Collaboration, The LIGO Laboratory'

DAQURLS = [
    'https://llocds.ligo-la.caltech.edu/data/chans/daq/',
    'https://lhocds.ligo-wa.caltech.edu/exports/running_config/h1/daqfiles/',
]


class Command(BaseCommand):
    """Update the CIS database by downloading and parsing DAQ INI files
    from the given URLs
    """
    help = __doc__.rstrip('\n ')

    def add_arguments(self, parser):
        """Add arguments to the command-line parser

        This function is only used for Django >= 1.8
        """
        parser.add_argument(
            'url', nargs='*', default=DAQURLS,
            help='URL to query for DAQ INI files, default: %(default)s')
        parser.add_argument('-i', '--ifo',
                            help='only process model files for this IFO')
        parser.add_argument(
            '-k', '--keytab', default=os.getenv('KRB5_KTNAME', None),
            help='path to kerberos keytab file, default: %(default)s')
        parser.add_argument(
            '-t', '--skip-update-tree-nodes', action='store_true',
            default=False, help='do not update tree nodes database after '
                                'update channels, default: %(default)s')

    def handle(self, url=[], ifo=None, keytab=None, **kwargs):
        """Update the CIS database from DAQ INI files in the given directories
        """
        verbose = kwargs.get('verbosity', 0)
        if isinstance(url, str):
            url = url.split(',')
        # authenticate with LIGO.ORG credentials
        try:
            ligo.org.klist(keytab=keytab)
        except ligo.org.KerberosError:
            ligo.org.kinit(keytab=keytab)
        # loop over each URL, download the INI file and update the channels
        for u in url:
            if verbose:
                print("Querying %s:" % u)
            for f, conf in functions.iterate_daq_ini_files(u):
                if ifo is not None and not f.lower().startswith(ifo.lower()):
                    continue
                mifo = ifo or os.path.basename(f[:2])
                if mifo.lower() in ['virgo', 'v0', 'v1']:
                    update_model = functions.update_virgo_model
                else:
                    update_model = functions.update_ligo_model
                update_model(conf, f, verbose=verbose, created_by='CDS')
                reset_queries()
        # now update the tree_node database for new channels
        if not kwargs.pop('skip_update_tree_nodes', False):
            functions.update_tree_nodes(verbose=verbose)
