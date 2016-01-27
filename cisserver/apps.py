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

"""App configuration for the Channel Information System App

This app should be added to `INSTALLED_APPS` as `'cisserver.apps.CisConfig'`
"""

from __future__ import unicode_literals

from django.apps import AppConfig

from . import version

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Brian Moe'
__version__ = version.version


class CisConfig(AppConfig):
    """`~django.apps.AppConfig` for the Channel Information system
    """
    name = 'cisserver'
    label = 'cis'
    verbose_name = 'Channel Information System'
