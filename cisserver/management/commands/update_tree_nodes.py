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

from django.core.management.base import BaseCommand

from ..functions import update_tree_nodes
from ... import version

__version__ = version.version
__author__ = 'Brian Moe, Duncan.macleod <duncan.macleod@ligo.org>'
__credits__ = 'The LIGO Scientific Collaboration, The LIGO Laboratory'


class Command(BaseCommand):
    """Update TreeNode database from current CIS channel table
    """
    help = __doc__.rstrip('\n ')

    def handle(self, *args, **kwargs):
        """Update tree nodes across the entire database
        """
        update_tree_nodes(verbose=kwargs.get('verbosity', 1))