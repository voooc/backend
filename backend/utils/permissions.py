#!/usr/bin/python
# -*- coding:utf-8 -*-
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        for i in request.user.get_roles_values():
            if i in ['SUPER']:
                return True
        # Write permissions are only allowed to the owner of the snippet.
        return obj.author == request.user


class IsOwnerOr(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        for i in request.user.get_roles_values():
            if i in ['SUPER']:
                return True
        # Write permissions are only allowed to the owner of the snippet.
        return obj.author == request.user


class IsAdminOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        for i in request.user.get_roles_values():
            if i in ['ADMIN', 'SUPER']:
                return True
        return False


class IsAdminUser(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        for i in request.user.get_roles_values():
            if i in ['ADMIN', 'SUPER']:
                return True
        return False


class IsSuperUser(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        for i in request.user.get_roles_values():
            if i in ['SUPER']:
                return True
        return False