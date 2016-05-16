Language: Python
Platform: Openstack Liberty

Implement virtual cluster orchestrator. Cluster consists of:
1) Single master node
2) Multiple worker nodes (number is specified by user, see below)
3) Private network between nodes
4) Router, that connects private network to public
5) Floating IP address assigned to master node in public network

-----  -----  -----
| M |  | W |  | W |  Virtual machines (M - master, W - worker)
-----  -----  -----
  |      |      |
  ---------------    Private network
         |
        ---
       ( x )         Virtual router (DNAT rule is inserted for M)
        ---
         |
  ---------------    External public network 

Requirements:
1) Orchestrator should use Keystone API (for authentication) and Heat API (for orchestration).
2) Heat API endpoint should be resolved from Keystone service catalog rather than hardcoded.
3) Orchestrator CLI arguments:
   a) Number of worker nodes to deploy.
   b) Heat stack name.
4) Orchestrator config file:
   a) image name and flavor for master node.
   b) image name and flavor for worker node.
   c) attributes for virtual networking, i.e. CIDR, public network ID.
   d) Keystone API endpoint.
5) Use oslo.config module for parsing CLI arguments and config file.
6) Keystone authentication credentials should be passed as environmental variables.
7) At the end of execution orchestrator should print assigned Floating IP address of master node to stdout.

Example:
$ ./orchestrator.py -n 3 mycluster
Master node Floating IP: 192.168.0.10

