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

import re

from django.db.models import (Model, CharField, ForeignKey, FloatField,
                              IntegerField, TextField, DateTimeField,
                              BooleanField, Q)
from django.conf import settings
from django.contrib.auth.models import User

from reversion import revisions as reversion

from rest_framework.reverse import reverse


class CisModel(Model):
    class Meta:
        abstract = True

    @classmethod
    def get_or_new(cls, **kwargs):
        """Find the class instance based on the `kwargs`, or create a new one
        """
        try:
            return cls.objects.get(**kwargs), False
        except cls.DoesNotExist:
            return cls(**kwargs), True


class Ifo(CisModel):
    """Model of a Laser Interferometer
    """
    name = CharField(max_length=10, null=False, unique=True)
    label = CharField(max_length=5,  null=False, unique=False)
    description = TextField(null=False)

    def __unicode__(self):
        return self.name


class Channel(CisModel):
    """Model for a data Channel

    A `Channel` is a single, recorded data stream read out from an `Ifo`.
    """
    DATATYPE = {
        0: "Undefined",
        1: "16-bit Integer",
        2: "32-bit Integer",
        3: "64-bit Integer",
        4: "32-bit Float",
        5: "64-bit Double",
        6: "32-bit Complex",
    }
    # key attributes
    ifo = ForeignKey(Ifo)
    subsystem = CharField(max_length=10, null=False)
    name = CharField(max_length=70, null=False, unique=True, db_index=True)
    # DAQ parameters
    gain = FloatField()
    slope = FloatField()
    offset = IntegerField()
    datatype = IntegerField()
    ifoid = IntegerField()
    acquire = IntegerField()
    units = CharField(max_length=10)
    dcuid = IntegerField()
    datarate = IntegerField()
    chnnum = IntegerField(null=True)
    # versioning
    created = DateTimeField(auto_now=True, null=False)
    createdby = CharField(max_length=30, null=False)
    source = CharField(max_length=30, db_index=True)
    # is it currently recorded?
    is_current = BooleanField(default=False, null=False)
    # is this a test-point (unrecorded channel)
    is_testpoint = BooleanField(default=False, null=False)

    def get_datatype_display(self):
        """String display of data type
        """
        return self.DATATYPE.get(self.datatype, self.datatype)

    def update_vals(self, vals):
        """Update the attributes for this `Channel`

        Parameters
        ----------
        vals : `list` of `tuples <tuple>`
            list of `(name, value)` attribute pairs

        Returns
        -------
        changed : `bool`
            whether object has changed
        """
        changed = False
        for attr, val in vals:
            old = getattr(self, attr)
            try:
                new = type(old)(val)
            except (ValueError, TypeError):
                # problem with casting
                # Go ahead and change -- let the model sort it out.
                #   OR
                # oldval is None -- one of val or old val is not None
                if val is not None or new is not None:
                    changed = True
                    setattr(self, attr, val)
            else:
                if old != new:
                    changed = True
            if changed:
                setattr(self, attr, val)
        return changed

    def subsystem_description(self):
        """Get the description for the `Subsytem` of this `Channel`

        Returns
        -------
        description : `str`
            the string description, or `'?'` if no description is found
        """
        try:
            return Subsystem.objects.get(label=self.subsystem).description
        except ValueError:
            return "?"

    def description(self):
        """The description of this `Channel`
        """
        name = self.name.split(':')[1]
        return ChannelDescription.get_or_new(name=name)[0]

    def sub_names(self, include_self=False):
        """Find the component names of this `Channel`

        Parameters
        ----------
        include_self : `bool`, optional, default: `False`
            include the full name of this channel (excluding the IFO prefix),
            along with the sub-parts

        Returns
        -------
        names : `list` of `str`
            a list of component sub-strings for this `Channel`
        """
        match = re.match(
            r'^(?P<ifo>[A-Z0-9]+):(?P<subsys>[A-Z]+)-(?P<rest>[A-Za-z0-9_]+)$',
            self.name)
        if match:
            names = [match.group(2)] + match.group(3).split('_')
        else:
            names = []
        if include_self:
            names.append(self.name.split(':')[1])
        return names

    def defined_descriptions(self):
        """Find all `ChannelDescription` entries for this `Channel`
        """
        return ChannelDescription.objects.filter(
            Q(name__in=self.sub_names(include_self=True)))

    def descriptions(self):
        """Find all `ChannelDescription` entries for this `Channel`
        """
        match = re.match(
            r'^(?P<ifo>[A-Z0-9]+):(?P<subsys>[A-Z]+)-(?P<rest>[A-Z0-9_]+)$',
            self.name)
        if match:
            return [ChannelDescription.get_or_new(name=name)[0] for
                    name in [match.group(2)] + match.group(3).split('_')]
        # XXX: need to deal with vacuum channels.
        return []

    @classmethod
    def user_query(cls, query=""):
        # Typed user query -> Q
        query = query.strip()
        if query:
            # Query language like LigoDV-Web
            # Spaces indicate AND, '|' indicates OR, AND has precedence over OR
            # terms are case insensitive.
            #  eg. H1: pem | H2: PSL
            #   is (*H1:* & *pem*) | (*H2:* | *PSL*)

            ors = []
            for term in query.split('|'):
                ands = [Q(name__icontains=aterm.strip()) for
                        aterm in term.split()]
                ors.append(reduce(Q.__and__, ands, Q()))
            q = reduce(Q.__or__, ors, Q())
        else:
            q = Q()

        return q

    def simulink_model_link(self):
        """Return the URL of the webview for this channels Simulink model
        """
        # Links only guaranteed for current acquired channels.
        if not (self.acquire and self.is_current):
            return None
        # LHO
        if self.name[0] in ['h', 'H']:
            return ('https://lhocds.ligo-wa.caltech.edu/simulink/'
                    '%s_slwebview.html' % self.source.lower())
        # LLO
        elif self.name[0] in ['l', 'L']:
            return ('https://llocds.ligo-la.caltech.edu/daq/simulink/'
                    '%s_slwebview.html' % self.source.lower())
        else:
            return None

    def get_absolute_url(self, request=None):
        return reverse("channel", args=[self.id], request=request)

    def revisions(self):
        return [v.field_dict for v in reversion.get_unique_for_object(self)]

    def __unicode__(self):
        return self.name

reversion.register(Channel)


class Subsystem(CisModel):
    """Instrumental sub-system for a `Channel` or set of `Channels`
    """
    name = CharField(max_length=10, null=False, unique=True)
    label = CharField(max_length=5,  null=False, unique=False)
    description = TextField(null=False)

    class Meta(CisModel.Meta):
        ordering = ["name"]

    def __unicode__(self):
        return self.name


class ChannelDescription(CisModel):
    """Description of a channel or sub-section of a channel name.
       This is a simple mapping of 'name' to text.
    """
    name = CharField(max_length=60, db_index=True, unique=True)
    desc = CharField(max_length=100)
    text = TextField(null=True, blank=True)
    created = DateTimeField(auto_now_add=True, null=False)
    modified = DateTimeField(auto_now=True, null=False)
    editor = ForeignKey(User, blank=True, null=True)

    def get_absolute_url(self, request=None):
        return reverse("api-description", args=[self.id], request=request)

    def revisions(self):
        return [v.field_dict for v in reversion.get_unique_for_object(self)]

    def __unicode__(self):
        return self.name

reversion.register(ChannelDescription)


class TreeNode(CisModel):
    # name -- sub-string of full channel name.
    # Unless this is a leaf node, then it is the full channel name.
    #   eg CHANNEL from L1:PSL-ODC_CHANNEL_OUT_DQ
    name = CharField(max_length=70, db_index=True)
    parent = ForeignKey("TreeNode", null=True)
    channel = ForeignKey("Channel", null=True)  # not NULL iff a leaf node

    # namepath: comma-sep list of ancestors' names
    # (technically redundant, used for optimization)
    # Is NULL (XXX or indeterminate?) for leaf nodes
    # Last name in list is self.name
    #   eg PSL,ODC,CHANNEL
    namepath = CharField(max_length=60, db_index=True, null=True)

    @classmethod
    def add_channel(cls, channel):
        """Add a copy of a channel to the database
        """
        if cls.objects.filter(channel=channel).count():
            return
        names = channel.sub_names()
        if not names:
            # This is some weirdo channel that doesn't have
            # recognizable sub-names.  Like a vacuum channel.
            # Ignore it.
            return
        node = cls(name=channel.name, channel=channel)
        node.parent = cls.node_with_path(names, create=True)
        node.save()

    @classmethod
    def node_with_path(cls, path, create=False):
        namepath = ",".join(path)
        try:
            return cls.objects.get(namepath=namepath)
        except cls.DoesNotExist:
            if not create:
                raise

        if not path:
            return None

        node = cls(name=path[-1], namepath=namepath)
        node.parent = cls.node_with_path(path[0:-1], create)
        node.save()
        return node


# Deprecated. TreeNode is a more descriptive name. Descriptions no longer used.
class Description(CisModel):
    name = CharField(max_length=60, db_index=True)
    fullname = CharField(max_length=60, null=True, db_index=True)
    shortdesc = CharField(max_length=60, null=True, db_index=True)
    text = TextField(null=True)
    parent = ForeignKey("Description", null=True)

    @classmethod
    def _add_standard(cls, name):
        if not name:
            return None
        lookedup = cls.objects.filter(fullname=name)
        if lookedup.count():
            return lookedup[0]
        new = cls(fullname=name)
        parentname, myname = new._split_standard_name()
        new.name = myname
        parent = new._add_standard(parentname)
        new.parent = parent
        new.save()
        return new

    @classmethod
    def add(cls, name):
        lookedup = cls.objects.filter(name=name)
        if lookedup.count():
            return lookedup[0]
        # what kind of channel is this?
        if re.match(r'^[A-Z0-9]+:[A-Z]+-[A-Z0-9_]+$', name):
            return cls._add_standard(name)
        elif re.match(r'^.VE-[A-Z0-9]+:[A-Z0-9]+$', name):
            # vacuum channel
            pass
        else:
            # who knows.
            pass
        return None

    def _split_standard_name(self):
        # (parent_fullname, my_shortname) for a standard channel.
        name = self.fullname

        if name.find(':') >= 0:
            # Actual, physical channel name.  Peel off IFO.
            # Need to deal with LVE-XX:XXX_XXX_XXX kinds of things.
            #
            # For physical channel names, fullname == name.
            return name[name.find(':')+1:], name

        locateUnderscore = name.rfind('_')
        if locateUnderscore >= 0:
            return name[:locateUnderscore], name[locateUnderscore+1:]

        locateDash = name.rfind('-')
        if locateDash >= 0:
            return name[:locateDash], name[locateDash+1:]

        return "", name

    def _parentName(self):
        # name of parent for std channel.
        name = self.name
        if name.find(':') >= 0:
            # Actual, physical channel name.  Peel off IFO.
            # Need to deal with LVE-XX:XXX_XXX_XXX kinds of things.
            return name[name.find(':')+1:]
        if name.rfind('_') >= 0:
            return name[:name.rfind('_')]
        if name.rfind('-') >= 0:
            return name[:name.rfind('-')]
        return ""

    def __unicode__(self):
        return self.name

reversion.register(Description)


# PEM Sensor web page has nice diagrams of where sensors are.
#
# Given a sensor name, we can generate a URL for one of these diagrams.
# We need a way to map CHANNEL_NAME => SENSOR_NAME
#
# A sensor name is a prefix of a channel name.  Given a list of all sensors,
# and a channel name, we find a sensor name that is a prefix of the
# channel name.
class PemSensor(CisModel):
    """A model of a Physical Environment Monitoring sensor
    """
    name = CharField(max_length=70, null=False, unique=True)

    @property
    def link(self):
        """The web URL for this `PemSensor`

        :type: `str`
        """
        return settings.PEM_SENSOR_DIAGRAM_URL_PATTERN.format(name=self.name)

    @classmethod
    def sensor_for_channel(cls, channel):
        """Find the `PemSensor` associated with the given channel name

        Parameters
        ----------
        channel : `str`, `Channel`
            name of channel who's sensor you want

        Returns
        -------
        sensor : `PemSensor`
            the first `PemSensor` found to associate with the given `Channel`
        """
        prefix_len = settings.PEM_SENSOR_MIN_LENGTH
        prefix = str(channel)[:prefix_len]
        candidates = cls.objects.filter(name__startswith=prefix)
        for candidate in candidates:
            if str(channel).startswith(candidate.name):
                return candidate
        return None
