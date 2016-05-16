#!/usr/bin/env python
"""Orchestrator code to create a heat stack."""

from datetime import date
from jinja2 import Template
from oslo_config import cfg
import sys
import time

import templates
import utils

auth_opts = [
    cfg.StrOpt('keystone_endpoint',
               help='Authentication Endpoint')
]

master_node_opts = [
    cfg.StrOpt('image_name',
               help='Image to use for Master node'),
    cfg.StrOpt('flavor',
               help='Flavor to use for Master node')
]

worker_node_opts = [
    cfg.StrOpt('image_name',
               help='Image to use for Worker node'),
    cfg.StrOpt('flavor',
               help='Flavor to use for Worker node')
]

network_group_opts = [
    cfg.StrOpt('private_network_cidr',
               help='CIDR to create private network'),
    cfg.StrOpt('public_network_id',
               help='Public network ID')
]

CONF = cfg.CONF
CONF.register_opts(auth_opts)
CONF.register_opts(master_node_opts, group='master')
CONF.register_opts(worker_node_opts, group='worker')
CONF.register_opts(network_group_opts, group='virtual_network')

CONF.register_cli_opt(cfg.IntOpt('n', help="Number of worker nodes"))
CONF.register_cli_opt(cfg.StrOpt('stack_name',
                                 help="Name of stack",
                                 positional=True))
CONF(sys.argv[1:])


def orchestrator(stack_name):
    """Create heat stack using the generated template.

    prints the value of floating_ip assigned to master node.
    param: name of stack
    """
    keystone = utils.get_keystone_client()
    heat_client = utils.get_heat_client(keystone)

    params = {}
    params['no_worker_nodes'] = CONF.n
    params['public_net_id'] = CONF.virtual_network.public_network_id
    params['private_net_cidr'] = CONF.virtual_network.private_network_cidr

    try:
        heat_template = get_heat_template(stack_name)

        param_dict = {"stack_name": stack_name,
                      "template": str(heat_template)}
        param_dict["parameters"] = params

        # Validating the generated template
        heat_client.stacks.validate(**param_dict)

        # Creating heat stack
        result = heat_client.stacks.create(**param_dict)
        stack_id = result['stack']['id']

        # Checking for status of the stack
        for x in xrange(0, 10):
            stack_status = heat_client.stacks.get(stack_id).status
            if "FAILED" in stack_status:
                raise Exception("Stack creation failed")
            if "COMPLETE" in stack_status:
                break
            time.sleep(5)

        # Get output from stack and print master_node floating IP value
        output_list = heat_client.stacks.get(stack_id).outputs
        for output in output_list:
            if isinstance(output, dict):
                if 'master_node_fip' in output['output_key']:
                    floating_ip = output['output_value']
                    print("Master node Floating IP: {}".format(floating_ip))

    except Exception as ec:
        raise ec


def get_heat_template(name):
    """Function generates heat template.

    :param: stack name - parsed from CLI
    :returns: heat template rendered using Jinja
    """
    cluster_obj = Cluster(name)
    para, res, out = Cluster.heat_template(cluster_obj,
                                           template=templates.cluster_template)
    template = Template(templates.heat_template)
    result = template.render(date_s=(date.today().strftime("%Y-%m-%d")),
                             paras=para,
                             resources=res,
                             outputs=out)
    return result


class Cluster(object):
    """Render heat template.

    parameter, resource and output fields of template
    are rendered by passing the corresponding values.
    Values for the parameters are parsed from CLI
    and orchestrator.conf file.
    """

    def __init__(self, name):
        """Read values from CONF and assign to local variables."""
        self.stack_name = name
        self.net_name = self.stack_name + "-private-network"
        self.subnet_name = self.stack_name + "-private-subnet"
        self.router_name = self.stack_name + "-router"
        self.master_image = CONF.master.image_name
        self.master_flavor = CONF.master.flavor
        self.worker_image = CONF.worker.image_name
        self.worker_flavor = CONF.worker.flavor

    @staticmethod
    def __param_heat(render, cls_obj):
        return render.render_parameter(cluster=cls_obj)

    @staticmethod
    def __resource_heat(render, cls_obj):
        return render.render_resources(cluster=cls_obj)

    @staticmethod
    def __output_heat(render, cls_obj):
        return render.render_output(cluster=cls_obj)

    @staticmethod
    def heat_template(cluster, template):
        """Render cluster heat template.

        :param cluster: object of Cluster class.
        :param template: the jinja template to be rendered.
        :returns: rendered template for param. resource and output.
        """
        render = utils.TemplateRender(template)
        param_json = Cluster.__param_heat(render, cluster)
        resource_json = Cluster.__resource_heat(render, cluster)
        output_json = Cluster.__output_heat(render, cluster)
        return (param_json, resource_json, output_json)

if __name__ == "__main__":

    CONF(default_config_files=['orchestrator.conf'])

    name_of_stack = CONF.stack_name

    # Creating stack and getting the return value
    orchestrator(name_of_stack)
