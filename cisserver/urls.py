# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2016)
#
# This file is part of cis.ligo.org
#
# cis.ligo.org is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cis.ligo.org is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cis.ligo.org.  If not, see <http://www.gnu.org/licenses/>

from django.conf.urls import (include, url)
from django.contrib import admin

from . import views

urlpatterns = [
    # home page
    url(r'^$',
        'cisserver.views.home', name='home'),
    # channels
    url(r'^channel/$',
        views.ChannelListView.as_view(), name="channels"),
    url(r'^channel/(?P<pk>\d+)$',
        views.ChannelDetailView.as_view(), name="channel"),
    url(r'^channel/byname/(?P<name>[A-Z0-9a-z_:-]+)$',
        "cisserver.views.channelByName", name="channel_by_name"),
    # ifos
    url(r'^ifo/$',
        views.IfoListView.as_view(), name="ifos"),
    url(r'^ifo/(?P<pk>\d+)$',
        views.IfoDetailView.as_view(), name="ifo"),
    # subsystems
    url(r'^subsystem/$',
        views.SubsystemListView.as_view(), name="subsystems"),
    url(r'^subsystem/(?P<pk>\d+)$',
        views.SubsystemDetailView.as_view(), name="subsystem"),
    # editing
    url(r'^edit/(?P<pk>\d+)$',
        'cisserver.views.edit', name="edit_values"),
    url(r'^editdescription/(?P<name>[A-Za-z0-9:_-]+)$',
        'cisserver.views.edit_description', name="edit_description"),
    # tree navigation
    url(r'^tree/$',
        "cisserver.views.tree", name="tree"),
    #url(r'^tree/select/(?P<selection>(.+))?$', "cisserver.views.tree",
    #    name="tree_select"),
    url(r'^tree/data/(?P<pk>(\d+|null))?$',
        "cisserver.views.tree_data", name="tree_data"),
    # testing
    #url(r'^test', "cisserver.views.test", name="test"),
    # admin
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', admin.site.urls, name="admin"),
    # api
    url(r'^api/', include('cisserver.api.urls'), name="api"),
    #url(r'^env', "cisserver.views.env"),
]
