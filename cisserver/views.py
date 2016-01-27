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

from django.http import (HttpResponse, HttpResponseRedirect)
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import render_to_response

from django.shortcuts import get_object_or_404

from django.views.generic import (DetailView, ListView)

from django.conf import settings

from django import forms
from django.utils import dateformat

from .models import (Channel, Ifo, Subsystem, TreeNode, ChannelDescription,
                     PemSensor)

import json


def home(request):
    return render_to_response("index.html", {'title': "Home"},
                              RequestContext(request))


class IfoListView(ListView):
    """`~django.views.generic.ListView` for an `~cisserver.models.Ifo`
    """
    context_object_name = "ifo_list"
    model = Ifo


class IfoDetailView(DetailView):
    """`~django.views.generic.DetailView` for an `~cisserver.models.Ifo`
    """
    context_object_name = "ifo"
    model = Ifo


class SubsystemListView(ListView):
    """`~django.views.generic.ListView` for a `~cisserver.models.Subsystem`
    """
    context_object_name = "subsystem_list"
    model = Subsystem


class SubsystemDetailView(DetailView):
    """`~django.views.generic.DetailView` for a `~cisserver.models.Subsystem`
    """
    context_object_name = "subsystem"
    model = Subsystem


class ChannelListView(ListView):
    """`~django.views.generic.ListView` for a `~cisserver.models.Channel`
    """
    context_object_name = "channel_list"
    model = Channel
    paginate_by = 40

    def get_context_data(self, **kwargs):
        context = super(ChannelListView, self).get_context_data(**kwargs)
        query = self.request.GET.get('qq', '')
        current_only = self.request.GET.get('current_only', '1')
        if current_only == "1":
            current_only = 1
            context["current_checked"] = "CHECKED"
        else:
            current_only = 0
            context["current_checked"] = ""
        context["title"] = "Channel List"
        context["query"] = query
        context["current_only"] = current_only
        return context


class ChannelDetailView(DetailView):
    """`~django.views.generic.DetailView` for a`~cisserver.models.Channel`
    """
    context_object_name = "channel"
    model = Channel

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        channel = context['channel']
        context["can_edit"] = check_can_edit(self.request,
                                             kwargs.get('object', None))

        # PEM Info Link
        sensor = PemSensor.sensor_for_channel(channel.name)
        if sensor:
            context["pem_link"] = sensor.link

        # XXX These links.... maybe they should be in the model?

        # INI file link
        model_link_pattern = settings.MODEL_INI_URLS_PATTERNS.get(
            channel.ifo.name, None)
        if model_link_pattern:
            context["model_link"] = model_link_pattern.format(
                model=channel.source)

        # Current Spectrum / Time series
        # Use spectrum if sample rate is >= 126, time series otherwise.

        # Only valid if channel is current and acquired.
        if channel.is_current and channel.acquire:
            if channel.datarate >= 126:
                spectrum_link_pattern = settings.SPECTRUM_URL_PATTERN
                if spectrum_link_pattern:
                    context["spectrum_link"] = spectrum_link_pattern.format(
                        channel=channel.name)
            else:
                time_series_link_pattern = settings.TIME_SERIES_URL_PATTERN
                if time_series_link_pattern:
                    context["time_series_link"] = (
                        time_series_link_pattern.format(channel=channel.name))

        return context


class EditChannelForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ('gain', 'slope', 'datatype', 'ifoid',
                  'acquire', 'offset', 'units', 'dcuid', 'datarate')


def check_can_edit(request, obj):
    # XXX lordy, this is a mess
    user = request.META.get('REMOTE_USER', None)
    if user is None:
        return False
    if user in settings.CIS_CAN_EDIT_DESCRIPTIONS:
        return True
#   Ummm..... user is a string.
#   if (isinstance(obj, ChannelDescription) and
#           obj.editor.username == user.username):
#       return True
#   if isinstance(obj, Channel) and obj.createdby == user.username:
#       return True
    return False


def edit(request, pk):
    context = {}
    channel = Channel.objects.get(id=pk)
    context['channel'] = channel
    if request.method == "GET":
        context['form'] = EditChannelForm(instance=channel)
    elif request.method == "POST":
        if request.POST.get('cancel'):
            return HttpResponseRedirect(reverse('channel', args=[channel.id]))
        form = EditChannelForm(request.POST, instance=channel)
        if form.is_valid():
            channel = form.save(commit=False)
            channel.createdby = request.META.get('REMOTE_USER', "unknown")
            # XXX authz
            channel.save()
            return HttpResponseRedirect(reverse('channel', args=[channel.id]))
        else:
            context['form'] = form
    else:
        # WHAT?
        raise Exception("unsupported method %s" % request.method)
    return render_to_response(
        'cis/edit.html', context, RequestContext(request))

textile_help_text = ("<a href=\"http://redcloth.org/hobix.com/textile/\" "
                     "target=\"_new\">textile markup</a>.")
markdown_help_text = ("The channel description markup syntax is called "
                      "<a href=\"http://daringfireball.net/projects/markdown/"
                      "syntax\" target=\"_new\">markdown</a>.")


def dictify(channel):
    timeformat = 'Y-m-d H:i:s T'
    return {
        'id': channel.id,
        'name': channel.name,
        'slope': channel.slope,
        'units': channel.units,
        'acquire': channel.acquire,
        'datatype': channel.datatype,
        'ifoid': channel.ifoid,
        'offset': channel.offset,
        'dcuid': channel.dcuid,
        'datarate': channel.datarate,
        'modified': dateformat.format(channel.created, timeformat),
        'ifo': channel.ifo.name,
        'subsystem': channel.subsystem,
        'source': channel.source,
        'resource': reverse('channel', args=[channel.id]),
    }


def tree(request, selection=None):
    context = {}
    return render_to_response(
        'cis/channel_tree.html', context, RequestContext(request))


def tree_data(request, pk=None):
    if pk:
        obj = TreeNode.objects.get(id=pk)
    else:
        # Fake root object.  DO NOT save() IT!
        obj = TreeNode(name="root")

    def dictify(node):
        d = {
            "name": node.name,
            "id": node.id or 0,
            "parentid": node.parent_id,
            }
        if TreeNode.objects.filter(parent_id=node.id).exists():
            d['children'] = True
        else:
            d['cid'] = node.channel_id
        return d

    children = [dictify(child) for child in
                TreeNode.objects.filter(parent=obj.id).order_by("name").all()]

    rv = {
        "name": obj.name,
        "id": obj.id or 0,
        "children": children,
        "parentid": obj.parent_id,
    }
    return HttpResponse(json.dumps(rv), content_type="application/json")


def channelByName(request, name):
    channel = get_object_or_404(Channel, name=name)
    return HttpResponseRedirect(reverse('channel', args=[channel.id]))


def test(request):
    context = {}
    return render_to_response(
        'cis/test.html', context, RequestContext(request))


def env(request):
    import os
    response = HttpResponse(content_type="text/html")
    d = os.environ
    d = request.META
    response.write("<html><body><table><tr><th>Key</th><th>Value</th></tr>\n")
    for key in d:
        response.write("<tr><td>%s</td><td>%s</td></tr>\n" % (key, d[key]))
    response.write("</table></body></html>")
    return response


class EditDescriptionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.fields['desc'].label = "Short Description"
        self.fields['text'].label = "Description (HTML)"

    class Meta:
        model = ChannelDescription
        fields = ('desc', 'text')


def edit_description(request, name):
    description = ChannelDescription.get_or_new(name=name)[0]
    can_edit = check_can_edit(request, description)
    if request.method == "GET":
        if "cancel" in request.GET:
            return render_to_response(
                'cis/description_fragment.html',
                {"description": description, 'can_edit': can_edit},
                RequestContext(request))
        form = EditDescriptionForm(instance=description)
    elif request.method == "POST":
        # XXX check can_edit.
        form = EditDescriptionForm(request.POST, instance=description)
        if form.is_valid():
            description = form.save(commit=False)
            description.editor = request.user
            description.save()
            return render_to_response(
                'cis/description_fragment.html',
                {"description": description, 'can_edit': can_edit},
                RequestContext(request))
    else:
        raise Exception("Unsupported method %r" % request.method)
    return render_to_response(
        "cis/description_edit_fragment.html",
        {'form': form, 'description': description},
        RequestContext(request))
