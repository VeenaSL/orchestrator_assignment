import mock
import unittest
import templates
from orchestrator import get_heat_template
from orchestrator import Cluster
from orchestrator import orchestrator

class Dummy_stack(object):

    def __init__(self, **kwargs):
        global create_failed
        self.id = "1234"
        if create_failed:
            self.status = "FAILED"
            create_failed = False
        else:
            self.status = "COMPLETE"
        self.outputs = [{"output_value":"10.0.0.5", "output_key": "master_node_fip"}]

class DummyStack(object):
    
    def validate(self, **kwargs):
        pass

    def create(self, **kwargs):
        return {"stack": {"id": "1234"}}

    def get(self, id, **kwargs):
        return Dummy_stack()

class DummyCatalog(object):

    def url_for(self, **kwargs):
        return 'dummy-url'

class DummyClient(object):

    def __init__(self, **kwargs):
        self.service_catalog = DummyCatalog()
        self.auth_token = "1223"

class DummyHeatClient(object):

    def __init__(self, **kwargs):
        self.stacks = DummyStack()

def dummy_heat_client(*args, **kwargs):
    return DummyHeatClient()

def dummy_keystone(*args, **kwargs):
    return DummyClient()

def dummy_template():
    template = {
        "parameters":"public_net_id",
        "resources":"private_network",
        "outputs":"master_node_fip"}
    return template

class Dummy_Cluster(object):

    def __init__(self, **kwargs):
        self.stack_name = "test-stack"
        self.net_name = self.stack_name + "-private-network"
        self.subnet_name = self.stack_name + "-private-subnet"
        self.router_name = self.stack_name + "-router"
        self.master_image = "cirros"
        self.master_flavor = "m1.tiny"
        self.worker_image = "cirros"
        self.worker_flavor = "m1.tiny"


class TestOrchestrator(unittest.TestCase):

    def cmp(self, a, b):
        return [c for c in a if c.isalpha()] == [c for c in b if c.isalpha()]

    def test_template(self):
        params = '''
  public_net_id:
    type: string
    description: ID or name of public network

  private_net_cidr:
    type: string
    description: CIDR of the private network

  no_worker_nodes:
    type: number
    description: Number of worker nodes to be created
    '''
        resource = '''
  private_network:
    type: OS::Neutron::Net
    properties:
      name: test-stack-private-network
      admin_state_up: True
      shared: False

  private_subnet:
    type: OS::Neutron::Subnet
    depends_on: private_network
    properties:
      name: test-stack-private-subnet
      network_id: { get_resource: private_network }
      cidr: { get_param: private_net_cidr }

  test_router:
    type: OS::Neutron::Router
    properties:
      name: test-stack-router
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
          name: test-stack_worker_node_%index%
          image: cirros
          flavor: m1.tiny
          networks:
            - uuid: { get_resource: private_network }

  master_node:
    type: OS::Nova::Server
    properties:
      name: test-stack_master_node
      image: cirros
      flavor: m1.tiny
      networks:
        - port: { get_resource: master_node_port }
    '''
        outputs = '''
  master_node_fip:
    value: { get_attr: [ master_node_floatingip, floating_ip_address ]}
    '''
        cluster_obj = Dummy_Cluster()
        para, res, out = Cluster.heat_template(cluster_obj, template=templates.cluster_template)
        self.assertEqual(True, self.cmp(para, params))
        self.assertEqual(True, self.cmp(res, resource))
        self.assertEqual(True, self.cmp(out, outputs))

    @mock.patch('utils.get_heat_client', side_effect=dummy_heat_client)
    @mock.patch('keystoneclient.service_catalog.ServiceCatalog.url_for')
    @mock.patch('utils.get_keystone_client', side_effect=dummy_keystone)
    def test_orchestrator(self, mock_heat, mock_url, mock_ks):
        try:
            global create_failed
            create_failed = False
            orchestrator("test")
        except Exception as ec:
            print ec
            self.assertTrue(False)

    @mock.patch('utils.get_heat_client', side_effect=dummy_heat_client)
    @mock.patch('keystoneclient.service_catalog.ServiceCatalog.url_for')
    @mock.patch('utils.get_keystone_client', side_effect=dummy_keystone)
    def test_orchestrator_fail(self, mock_heat, mock_url, mock_ks):
        global create_failed
        create_failed = True
        with self.assertRaises(Exception):
            orchestrator("test")

if __name__ == '__main__':
    unittest.main()
