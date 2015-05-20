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

"""RESTful API views for CIS
"""

import logging
import re

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import serializers
from rest_framework import permissions
from rest_framework import generics

from django.http import Http404
from django.conf import settings
from django.core.exceptions import PermissionDenied

from .. import version
from ..models import (Channel, ChannelDescription as Description)

logger = logging.getLogger(__name__)

__version__ = version.version
__author__ = 'Brian Moe, Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'The LIGO Scientific Collaboration, The LIGO Laboratory'


class CisApiPermission(permissions.BasePermission):
    """General permissions on the CIS API.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return True

    def has_object_permission(self, request, view, obj):
        """Determine whether the user has permission to request this object
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        if hasattr(obj, 'editor') and obj.editor == request.user:
            return True

        if (hasattr(obj, 'createdby') and
                obj.createdby == request.user.username):
            return True

        if (isinstance(obj, Description) and
                request.user.username in settings.CIS_CAN_EDIT_DESCRIPTIONS):
            return True

        return False


class DojoJsonRestApiView(generics.ListCreateAPIView):
    """A ListCreateAPIView that understands Range

    Headers as used in Dojo's dojo.store.JsonRest data store.
    """
    # XXX Probably should target the mixin(s) whence these methods originate.
    empty_error = "Empty list and '%(class_name)s.allow_empty' is False."

    def list(self, request, *args, **kwargs):
        qrange = request.META.get("HTTP_RANGE")
        if not qrange:
            return generics.ListCreateAPIView.list(self, request, *args, **kwargs)
            # return super(generics.ListCreateAPIView, self).list(
            #     request, *args, **kwargs)

        queryset = self.get_queryset()
        self.object_list = self.filter_queryset(queryset)

        # Default is to allow empty querysets.  This can be altered by setting
        # `.allow_empty = False`, to raise 404 errors on empty querysets.
        allow_empty = self.get_allow_empty()
        if not allow_empty and not self.object_list:
            class_name = self.__class__.__name__
            error_msg = self.empty_error % {'class_name': class_name}
            raise Http404(error_msg)

        start, end = re.match("items=(\d+)-(\d+)", qrange).groups()
        start = int(start)
        end = int(end)+1
        full_count = self.object_list.count()
        self.object_list = self.object_list[start:end]
        this_count = len(self.object_list)
        serializer = self.get_serializer(self.object_list, many=True)

        content_range = "items %s-%s/%s" % (start, start+this_count-1, full_count)

        return Response(serializer.data, headers={'Content-Range': content_range})


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel

    descriptions = serializers.SerializerMethodField('get_descriptions')
    displayurl = serializers.SerializerMethodField('get_displayurl')
    url = serializers.SerializerMethodField('get_url')
    ifo = serializers.SerializerMethodField('get_ifoname')
    status = serializers.SerializerMethodField('get_status')

    def get_descriptions(self, obj):
        request = self.context.get('request', None)
        return reverse('api-channeldescriptions', args=[obj.pk], request=request)

    def get_displayurl(self, obj):
        request = self.context.get('request', None)
        return reverse('channel', args=[obj.pk], request=request)

    def get_url(self, obj):
        request = self.context.get('request', None)
        return reverse('api-channel', args=[obj.pk], request=request)

    def get_ifoname(self, obj):
        return obj.ifo.name

    def get_status(self, obj):
        if not obj.is_current:
            return "obsolete"
        elif obj.acquire == 0:
            return "testpoint"
        return "acquired"


class ChannelList(DojoJsonRestApiView):
    """This resource represents all channels in the Channel Information System.

    ### GET PARAMS
    When retrieving Channels, you may use the following query parameters:

    * `q=RE` : Query on channel name against regular expression, RE.
    * `sort=S` : Sort channels based on column, eg: -name
    * `page_size=N`: Paginated results should have N channels per page

    This resource also conforms to Dojo's dojo.store.JsonRest API with
    respect to partial retrievals specified via `Range:` request headers.
    See [Dojo Documentation on Json Rest](
    http://dojotoolkit.org/reference-guide/1.8/dojo/store/JsonRest.html).
    """
    permission_classes = (CisApiPermission,)

    model = Channel
    serializer_class = ChannelSerializer

    paginate_by = 20
    paginate_by_param = 'page_size'

    def post(self, request):
        if not request.user.is_staff:
            pass
        raise PermissionDenied()

    def pre_save(self, obj):
        obj.createdby = self.request.user.username

    def filter_queryset(self, queryset):
        request = self.request

        query = request.GET.get('q', '')
        current_only = request.GET.get('current_only', "1") == "1"
        queryset = queryset.filter(Channel.user_query(query))
        if current_only:
            queryset = queryset.filter(is_current=1)

        sort = request.GET.get('sort', '')
        if sort:
            # Some fields are named slightly differently in our grid.
            # XXX this is not general.
            sort = sort.replace("_item", "name").replace("modified", "created")
            for s in sort.split(','):
                # Need strip() as Dojo forgets to encode the '+'
                # by the time it gets here,  it is decoded as ' '
                queryset = queryset.order_by(s.strip())

        return queryset


class ChannelDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (CisApiPermission,)

    model = Channel
    serializer_class = ChannelSerializer
    slug_field = 'name'
    slug_url_kwarg = 'name'

    createdby = serializers.CharField(read_only=True, source='createdby')

    def pre_save(self, obj):
        obj.createdby = self.request.user.username


class Cis(APIView):
    """Channel Information System Root Resource
    """
    def get(self, request, format=None):
        return Response({
            'channels': reverse('api-channels', request=request, format=format),
            'descriptions': reverse('api-descriptions', request=request,
                                    format=format),
        })


class DescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Description

    created = serializers.DateTimeField(source='created', read_only=True)
    modified = serializers.DateTimeField(source='modified', read_only=True)
    editor = serializers.CharField(source='editor', read_only=True)
    url = serializers.SerializerMethodField('get_url')

    def get_url(self, obj):
        request = self.context.get('request', None)
        return reverse('api-description', args=[obj.pk], request=request)


class DescriptionList(DojoJsonRestApiView):
    model = Description
    serializer_class = DescriptionSerializer

    paginate_by = 20
    paginate_by_param = 'page_size'


class DescriptionDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Description
    serializer_class = DescriptionSerializer
    slug_field = 'name'
    slug_url_kwarg = 'name'

    def pre_save(self, obj):
        # XXX Fails if anonymous user, pass is probably not right.
        # Need to think about this.
        try:
            obj.editor = self.request.user
        except Exception:
            pass


class ChannelDescriptions(APIView):
    def get(self, request, name=None, pk=None):
        if name is None and pk is None:
            raise Exception('bitey')
        if name is not None:
            channel = Channel.objects.filter(name=name)
        else:
            channel = Channel.objects.filter(pk=pk)
        if not channel.count():
            raise Http404
        s = DescriptionSerializer(channel[0].defined_descriptions(),
                                  context={'request': request})
        return Response(s.data)
