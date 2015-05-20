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
import warnings
import sys
from os.path import (basename, splitext)

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

from django.db.utils import IntegrityError

from ..models import (Channel, Ifo)
from .. import version

__version__ = version.version
__author__ = 'Brian Moe, Duncan.macleod <duncan.macleod@ligo.org>'
__credits__ = 'The LIGO Scientific Collaboration, The LIGO Laboratory'


def update_ligo_model(inifile, modelname=None, verbose=False):
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
    if isinstance(inifile, file):
        if not modelname:
            raise ValueError("model name required")
        cp.readfp(inifile)
    else:
        modelname = splitext(basename(inifile))[0]
        cp.read(inifile)

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
        sys.stdout.flush()
        channel, created = Channel.get_or_new(name=name)
        changed = channel.update_vals(cp.items(name))
        if changed or created:
            if created:
                # XXX super-risky
                try:
                    channel.ifo = Ifo.objects.filter(name=modelname[0:2])[0]
                except IndexError:
                    channel.ifo = Ifo(name=modelname[0:2])
                    channel.ifo.save()
                    if verbose > 1:
                        print('    Created IFO %s' % channel.ifo.name)
                if verbose > 1:
                    print("    Created %s" % channel.name)
            elif verbose > 1:
                print("    Updated %s" % channel.name)
            try:
                channel.save()
            except IntegrityError as e:
                warnings.warn("IntegrityError [%s]: %s"
                              % (channel.name, str(e)))
        if verbose == 1:
            print("Updating %s: %d/%d" % (modelname, i+1, n), end='\r')
    if verbose == 1:
        print("Updating %s: %d/%d" % (modelname, n, n))


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
