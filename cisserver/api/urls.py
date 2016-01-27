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

"""Define URL redirects for CIS

The URLS are redirected as follows:

- ``/channel/``: show list of all `Channels <Channel>`
- ``/channel/<name>``: show details of a single `Channel`
- ``/channel/<name>/descriptions``: show descriptions for a `Channel`
- ``/description/``: show list of all descriptions
- ``/description/<name>`: show details of a single `Description`
"""

from django.conf.urls import (patterns, url)
from django.contrib import admin
admin.autodiscover()

from .views import (Cis, ChannelList, ChannelDetail, DescriptionList,
                    DescriptionDetail, ChannelDescriptions)
from .. import version

__version__ = version.version
__author__ = 'Brian Moe, Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'The LIGO Scientific Collaboration, The LIGO Laboratory'

urlpatterns = patterns(
    'cisserver.api.views',
    # Server root
    url(r'^$',
        Cis.as_view(),
        name='api-root'),
    # View list of channels
    url(r'^channel/$',
        ChannelList.as_view(),
        name="api-channels"),
    # View single channel
    url(r'^channel/((?P<pk>\d+)|(?P<name>[^\d][^/]+))$',
        ChannelDetail.as_view(),
        name="api-channel"),
    # View list of descriptions for a single channel
    url(r'^channel/((?P<pk>\d+)|(?P<name>[^\d][^/]+))/descriptions$',
        ChannelDescriptions.as_view(),
        name="api-channeldescriptions"),
    # View all descriptions
    url(r'^description/$',
        DescriptionList.as_view(),
        name="api-descriptions"),
    # View single description
    url(r'^description/((?P<pk>\d+)|(?P<name>[^\d][^/]+))$',
        DescriptionDetail.as_view(),
        name="api-description"),
)
