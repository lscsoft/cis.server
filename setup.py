#!/usr/bin/env python
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

import os

from setuptools import (find_packages, setup)
from setuptools.command import (build_py, egg_info)

from distutils import log

PACKAGENAME = 'cisserver'
PROVIDES = 'cisserver'
AUTHOR = 'Brian Moe, Duncan Macleod'
AUTHOR_EMAIL = 'duncan.macleod@ligo.org'
LICENSE = 'GPLv3'
VERSION_PY = os.path.join(PROVIDES.replace('.', os.path.sep), 'version.py')

cmdclass = {}


# -----------------------------------------------------------------------------
# Custom builders to write version.py

class GitVersionMixin(object):
    """Mixin class to add methods to generate version information from git.
    """
    def write_version_py(self, pyfile):
        """Generate target file with versioning information from git VCS
        """
        log.info("generating %s" % pyfile)
        import vcs
        gitstatus = vcs.GitStatus()
        try:
            with open(pyfile, 'w') as fobj:
                gitstatus.write(fobj, author=AUTHOR, email=AUTHOR_EMAIL)
        except:
            if os.path.exists(pyfile):
                os.unlink(pyfile)
            raise
        return gitstatus

    def update_metadata(self):
        """Import package base and update distribution metadata
        """
        import cisserver
        self.distribution.metadata.version = cisserver.__version__
        desc, longdesc = cisserver.__doc__.split('\n', 1)
        self.distribution.metadata.description = desc
        self.distribution.metadata.long_description = longdesc.strip('\n')


class CisBuildPy(build_py.build_py, GitVersionMixin):
    """Custom build_py command to deal with version generation
    """
    def __init__(self, *args, **kwargs):
        build_py.build_py.__init__(self, *args, **kwargs)

    def run(self):
        try:
            self.write_version_py(VERSION_PY)
        except ImportError:
            raise
        except:
            if not os.path.isfile(VERSION_PY):
                raise
        self.update_metadata()
        build_py.build_py.run(self)

cmdclass['build_py']= CisBuildPy


class CisEggInfo(egg_info.egg_info, GitVersionMixin):
    """Custom egg_info command to deal with version generation
    """
    def finalize_options(self):
        try:
            self.write_version_py(VERSION_PY)
        except ImportError:
            raise
        except:
            if not os.path.isfile(VERSION_PY):
                raise
        if not self.distribution.metadata.version:
            self.update_metadata()
        egg_info.egg_info.finalize_options(self)

cmdclass['egg_info']= CisEggInfo


# -----------------------------------------------------------------------------
# Run setup

packagenames = find_packages()
scriptsdir = 'bin'
scripts = [os.path.join(scriptsdir, exe) for
           exe in list(os.walk(scriptsdir))[0][2]]

setup(
    # distribution metadata
    name=PACKAGENAME,
    provides=[PROVIDES],
    version=None,
    description=None,
    long_description=None,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    url=None,
    # package metadata
    packages=packagenames,
    include_package_data=True,
    scripts=scripts,
    cmdclass=cmdclass,
    setup_requires=[
        'GitPython',
        'jinja2',
    ],
    install_requires=[
        'django >= 1.7',
        'django-reversion',
        'mysql-python'
    ],
    requires=[
        'django',
        'djangorestframework',
        'MySQLdb',
        'markdown',
    ],
    use_2to3=True,
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Environment :: Web Environment',
        'Framework :: Django',
    ],
)
