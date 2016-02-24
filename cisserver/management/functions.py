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

"""Functions assicated with management commands for `cisserver`
"""

from __future__ import print_function
import warnings
import sys
import re
from os.path import (basename, splitext, join)

try:
    from urllib2 import HTTPError
except ImportError:
    from urllib.error import HTTPError

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

from django.db.utils import IntegrityError
from django.db import reset_queries

from reversion import revisions as reversion

import ligo.org

from bs4 import BeautifulSoup

from ..models import (Channel, Ifo, Subsystem, TreeNode)
from .. import version

__version__ = version.version
__author__ = 'Brian Moe, Duncan.macleod <duncan.macleod@ligo.org>'
__credits__ = 'The LIGO Scientific Collaboration, The LIGO Laboratory'


def create_ifo_and_subsystem(channel, modelname, verbose=0):
    try:
        channel.ifo
    except AttributeError:
        newifo = True
    else:
        newifo = not channel.ifo
    try:
        channel.subsystem
    except AttributeError:
        newsubsystem = True
    else:
        newsubsystem = not channel.subsystem
    # parse name
    if newifo or newsubsystem:
        name = channel.name
        # parse channel name
        try:
            match = Channel.re_name.match(name).groupdict()
        except AttributeError as e:
            e.args = ('Cannot parse IFO and subsystem from channel name %r'
                      % name,)
            raise
        ifo = match['ifo'] or modelname[:2]
    modified = False
    # find/create IFO
    if newifo and ifo is not None:
        try:
            channel.ifo = Ifo.objects.get(name=ifo)
        except Ifo.DoesNotExist:
            ifo = Ifo(name=ifo)
            ifo.save()
            channel.ifo = ifo
            if verbose > 1:
                print('    Created IFO %s [%d]'
                      % (channel.ifo.name, channel.ifo.id))
        modified = True
    # find/create Subsystem
    if newsubsystem and match.get('subsystem') is not None:
        try:
            channel.subsystem = Subsystem.objects.get(
                name=match['subsystem']).name
        except Subsystem.DoesNotExist:
            subsystem = Subsystem(name=match['subsystem'])
            subsystem.save()
            channel.subsystem = subsystem.name
            if verbose > 1:
                print('    Created subsystem %s'
                      % channel.subsystem.name)
        modified = True
    return modified


@reversion.create_revision()
def update_ligo_model(inifile, modelname=None, verbose=False, created_by=None):
    """Update the LIGO channels from the given INI file

    Parameters
    ----------
    inifile : `str`, `file`-like
        path to INI file on disk, or an open file
    modelname : `str`
        the name of the front-end model. Only required if `inifile` is
        given as an open file
    """
    cp = ConfigParser()
    # read file-like object
    try:
        if not modelname:
            try:
                modelname = inifile.name
            except AttributeError as e:
                e.args = ("Cannot parse model name from file-like object, "
                          "please pass modelname=<str>",)
                raise
        cp.readfp(inifile)
    # or read str pointing to file
    except AttributeError:
        modelname = inifile
        cp.read(inifile)
    modelname = splitext(basename(modelname))[0].upper()
    reversion.set_comment(modelname)

    # DEFAULT section is probably not capitalized.
    # Find uncapitalized DEFAULT section and include its values.
    # (Python will not see uncapitalized default section)
    if 'default' in cp.sections():
        cp.defaults().update(dict(cp.items('default')))
        cp._sections.pop('default')
    cp.defaults().update(source=modelname)

    if verbose > 1:
        print("Updating %s:" % modelname)
    elif verbose:
        print("Updating %s:" % modelname, end='\r')
    n = len(cp._sections.keys())

    for i, name in enumerate(cp.sections()):
        # find/create Channel
        try:
            channel = Channel.objects.get(name=name)
        except Channel.DoesNotExist:
            channel = Channel(name=name)
            created = True
        else:
            created = False
        finally:
            changed = create_ifo_and_subsystem(channel, modelname,
                                               verbose=verbose)
        params = dict(cp.items(name))
        params['is_current'] = params.get('acquire', 0) > 0
        if created_by is not None:
            params['createdby'] = created_by
        changed |= channel.update_vals(params.iteritems())
        if changed or created:
            channel.save()
            if created and verbose > 1:
                print("    Created %s" % channel.name)
            elif changed and verbose > 1:
                print("    Updated %s" % channel.name)
        if verbose == 1:
            print("Updating %s: %d/%d" % (modelname, i+1, n), end='\r')
    if verbose == 1:
        print("Updating %s: %d/%d" % (modelname, n, n))


@reversion.create_revision()
def update_virgo_model(inifile, modelname=None, verbose=False):
    """Update the Virgo channels from the given INI file

    Parameters
    ----------
    inifile : `str`, `file`-like
        path to INI file on disk, or an open file
    modelname : `str`
        the name of the front-end model. Only required if `inifile` is
        given as an open file
    """
    raise NotImplementedError("Parsing Virgo INI files has "
                              "not been implemented yet.")


def update_tree_nodes(verbose=False):
    """Update the `TreeNode` database give a new set of channels
    """
    current = Channel.objects.filter(is_current=True)
    n = current.count()
    if verbose:
        print("Checking channels:", end='\r')
    add = TreeNode.add_channel
    for i, channel in enumerate(current.iterator()):
        add(channel)
        reset_queries()
        if verbose:
            print("Checking channels: [%d/%d]" % (i+1, n), end='\r')
    if verbose:
        print("Checking channels: [%d/%d]" % (n, n))


reini = re.compile('ini\Z')

def iterate_daq_ini_files(url):
    """Iterator over DAQ INI files

    Yeilds
    ------
    (`str`, `file`)
        the name and contents of each INI file found at the URL
    """
    try:
        f = ligo.org.request(url)
    except HTTPError as e:
        e.args = ('%s: %r' % str(e), url,)
        raise
    soup = BeautifulSoup(f, "html.parser")
    for a in soup.find_all('a', text=reini):
        ini = a.attrs['href']
        content = ligo.org.request(join(url, ini))
        yield ini, content
