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

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.utils.decorators import available_attrs
from django.utils.http import urlquote
from django.shortcuts import redirect

import logging
from functools import wraps


class LigoShibbolethMiddleware(RemoteUserMiddleware):
    """Middleware layer for LIGO.ORG Shibboleth authentication
    """
    if hasattr(settings, 'SHIB_AUTHENTICATION_IDENTITY_HEADER'):
        header = settings.SHIB_AUTHENTICATION_IDENTITY_HEADER
    else:
        header = 'REMOTE_USER'

    def process_request(self, request):
        logger = logging.getLogger(
            'ligodjangoauth.LigoShibbolethMiddleware.process_request')
        logger.debug('invoked')
        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The LigoShibbolethMiddlware auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the LigoShibbolethMiddleware class.")
        try:
            username = request.META[self.header]
            logger.debug('found username %s' % username)
        except KeyError:
            # If specified header doesn't exist then return (leaving
            # request.user set to AnonymousUser by the
            # AuthenticationMiddleware).
            logger.warn('could not find %s' % self.header)
            return

        # we are not using or relying on Django sessions - always authenticate
        user = auth.authenticate(identity=username, request=request)
        if user:
            # User is valid.  Set request.user
            request.user = user


class LigoShibbolethAuthBackend(RemoteUserBackend):
    """Backend for LIGO.ORG Shibboleth authentication
    """
    if hasattr(settings, 'ADMIN_GROUP_HEADER'):
        header = settings.ADMIN_GROUP_HEADER
    else:
        header = 'isMemberOf'

    if hasattr(settings, 'ADMIN_GROUP'):
        adminGroup = settings.ADMIN_GROUP
    else:
        adminGroup = 'Communities:LVC:LVCGroupMembers'

    def authenticate(self, identity, request):
        """Authenticate a user
        """
        logger = logging.getLogger(
            'ligodjangoauth.LigoShibbolethAuthBackend.authenticate')
        logger.debug('invoked with identity %s' % identity)
        if not identity:
            return

        # create the user object
        user, created = User.objects.get_or_create(username=identity)

        # This is different from system version,
        # which ALWAYS reconciles permissions.
        if created:
            # reconcile the authorization in headers with the
            # user object attributes, the default is no privileges
            user.is_staff = False
            user.is_superuser = False

            try:
                groups = request.META[self.header].split(';')
            except KeyError:
                pass
            else:
                if self.adminGroup in groups:
                    user.is_staff = True
                    user.is_superuser = True

            user.save()
            logger.debug('saved user object with identity %s' % identity)

        return user


def user_passes_test(
        test_func,
        login_url=getattr(settings, 'SHIB_AUTHENTICATION_SESSION_INITATOR',
                          None),
        redirect_field_name="target"):
    """Check whether a user can authenticate

    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.

    Parameters
    ----------
    test_func : `callable`
        function that returns the authentication state for a given user
    login_url : `str`
        URL string for login redirect
    redirect_field_name : `str`
        name of HTTP redirect field
    """
    def decorated_method(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            path = urlquote(
                request.build_absolute_uri(request.get_full_path()))
            return HttpResponseRedirect(
                '%s?%s=%s' % (login_url, redirect_field_name, path))
        return wraps(
            view_func, assigned=available_attrs(view_func))(_wrapped_view)
    return decorated_method


def login_required(function=None, redirect_field_name='target'):
    """Check whether a user is logged in

    This method is a decorator, checking that a user is logged in,
    and redirecting to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated(),
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def admin_required(f):
    """Decorator for a `View` that requires authentication

    Should only be used to decorate view functions that require
    authentication and membership in the admin group.

    Assumes args[0] passed to the wrapped function f is the Django
    request object passed into a view.
    """
    @wraps(f)
    def wrapper(*args, **kwds):
        if hasattr(settings, 'ADMIN_GROUP_HEADER'):
            header = settings.ADMIN_GROUP_HEADER
        else:
            header = 'isMemberOf'
        if hasattr(settings, 'ADMIN_GROUP'):
            admin_group_name = settings.ADMIN_GROUP
        else:
            admin_group_name = 'Communities:LVC:LVCGroupMembers'

        request = args[0]

        user_groups = request.META.get(header, None)
        if not user_groups:
            return redirect('views.admin_only')

        user_groups = user_groups.split(';')

        if admin_group_name not in user_groups:
            return redirect('views.admin_only')

        return f(*args, **kwds)
    return wrapper
