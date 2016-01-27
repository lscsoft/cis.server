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

"""Admin configuration for CIS Server
"""

from django.contrib import admin

from reversion.admin import VersionAdmin

from . import version
from .models import (Channel, Ifo, Subsystem, Description, ChannelDescription)

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Brian Moe'
__version__ = version.version


class ChannelAdmin(VersionAdmin):
    """`VersionAdmin` for the `~cisserver.models.Channel` model
    """
    search_fields = ['name']

admin.site.register(Channel, ChannelAdmin)


class ChannelDescriptionAdmin(VersionAdmin):
    """`VersionAdmin` for the `~cisserver.models.ChannelDescription` model
    """
    search_fields = ['name']

admin.site.register(ChannelDescription, ChannelDescriptionAdmin)


class IfoAdmin(VersionAdmin):
    """`VersionAdmin` for the `~cisserver.models.Ifo` model
    """
    list_display = ('name', 'description')

admin.site.register(Ifo, IfoAdmin)


class SubsystemAdmin(VersionAdmin):
    """`VersionAdmin` for the `~cisserver.models.Subsystem` model
    """
    list_display = ('name', 'description')

admin.site.register(Subsystem, SubsystemAdmin)


class DescriptionAdmin(VersionAdmin):
    """`VersionAdmin` for the `~cisserver.models.Description` model
    """
    list_display = ('fullname',)

admin.site.register(Description, DescriptionAdmin)
