#!/usr/bin/env python
"""Utility file for orchestrator."""

from heatclient import client as heatclient
from jinja2 import Template
import keystoneclient.v2_0.client as ksclient
import os
import pprint


def get_keystone_client():
    """Get keystone client."""
    # Reading authentication credentials from os environment
    user_name = os.environ['OS_USERNAME']
    passwd = os.environ['OS_PASSWORD']
    auth_url = os.environ['OS_AUTH_URL']
    project_id = os.environ['OS_TENANT_NAME']

    # Creating keystone client using the credentials
    keystone = ksclient.Client(auth_url=auth_url,
                               username=user_name,
                               password=passwd,
                               tenant_name=project_id)
    return keystone


def get_heat_client(keystone_client):
    """Get heat client."""
    # Obtaining heat endpoint
    heat_endpoint = keystone_client.service_catalog.url_for(
        service_type="orchestration", endpoint_type='public')

    # Creating Heat client using heat endpoint
    heat_client = heatclient.Client('1', endpoint=heat_endpoint,
                                    token=keystone_client.auth_token)
    return heat_client


class DictDotLookup(object):
    """Creates objects that behave much like a dictionaries.

    allow nested key access using object '.' (dot) lookups.
    """

    def __init__(self, d):
        """Modify dict to uswith dot."""
        for k in d:
            if isinstance(d[k], dict):
                self.__dict__[k] = DictDotLookup(d[k])
            elif isinstance(d[k], (list, tuple)):
                l = []
                for v in d[k]:
                    if isinstance(v, dict):
                        l.append(DictDotLookup(v))
                    else:
                        l.append(v)
                self.__dict__[k] = l
            else:
                self.__dict__[k] = d[k]

    def __getitem__(self, name):
        """Magic method for getitem."""
        if name in self.__dict__:
            return self.__dict__[name]

    def __iter__(self):
        """Magic method for iter."""
        return iter(self.__dict__.keys())

    def __repr__(self):
        """Magic method for repr."""
        return pprint.pformat(self.__dict__)


class TemplateRender(DictDotLookup):
    """Template render using jinja."""

    def __init__(self, template_dict):
        """Template render using jinja."""
        DictDotLookup.__init__(self, template_dict)
        self.param_render = Template(self.parameters) if self.parameters else None
        self.resource_render = Template(self.resources) if self.resources else None
        self.output_render = Template(self.outputs) if self.outputs else None

    def render_parameter(self, **args):
        """Render Parameter of template."""
        return (self.param_render.render(**args)
                if self.param_render else None)

    def render_resources(self, **args):
        """Render resource of template."""
        return (self.resource_render.render(**args)
                if self.resource_render else None)

    def render_output(self, **args):
        """Render output of template."""
        return (self.output_render.render(**args)
                if self.output_render else None)

    def render_all(self, **args):
        """Render param, resource and output."""
        return self.render_parameter(**args), \
            self.render_resources(**args), \
            self.render_resources(**args)
