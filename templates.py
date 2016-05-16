cluster_template = {
  "parameters":
  '''
  public_net_id:
    type: string
    description: ID or name of public network

  private_net_cidr:
    type: string
    description: CIDR of the private network

  no_worker_nodes:
    type: number
    description: Number of worker nodes to be created
  ''',
  "resources":
  '''
  private_network:
    type: OS::Neutron::Net
    properties:
      name: {{cluster.net_name}}
      admin_state_up: True
      shared: False

  private_subnet:
    type: OS::Neutron::Subnet
    depends_on: private_network
    properties:
      name: {{cluster.subnet_name}}
      network_id: { get_resource: private_network }
      cidr: { get_param: private_net_cidr }

  test_router:
    type: OS::Neutron::Router
    properties:
      name: {{cluster.router_name}}
      admin_state_up: True
      external_gateway_info:
        network: { get_param: public_net_id }

  test_router_connect:
    type: OS::Neutron::RouterInterface
    properties:
      router_id: { get_resource: test_router }
      subnet_id: { get_resource: private_subnet }

  master_node_port:
    type: OS::Neutron::Port
    properties:
      network: { get_resource: private_network }
      fixed_ips:
        - subnet: { get_resource: private_subnet }

  master_node_floatingip:
    type: OS::Neutron::FloatingIP
    properties:
      floating_network: { get_param: public_net_id }
      port_id: { get_resource: master_node_port }

  worker_nodes:
    type: OS::Heat::ResourceGroup
    properties:
      count: { get_param: no_worker_nodes }
      resource_def:
        properties:
        type: OS::Nova::Server
        properties:
          name: {{cluster.stack_name}}_worker_node_%index%
          image: {{cluster.worker_image}} 
          flavor: {{cluster.worker_flavor}}
          networks: 
            - uuid: { get_resource: private_network }

  master_node:
    type: OS::Nova::Server
    properties:
      name: {{cluster.stack_name}}_master_node
      image: {{cluster.master_image}}
      flavor: {{cluster.master_flavor}}
      networks: 
        - port: { get_resource: master_node_port }
  ''',
  "outputs":
  '''
  master_node_fip:
    value: { get_attr: [ master_node_floatingip, floating_ip_address ]}
  '''
}
heat_template = '''
heat_template_version: 2015-10-15 

description: >
  HOT template to create cluster

parameters:
  {%- for p in paras %}{{p}}{% endfor %}
resources:
  {%- for r in resources %}{{r}}{% endfor %}
outputs:
  {%- for o in outputs %}{{o}}{% endfor -%}
  '''

