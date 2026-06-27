"""Multi-host deployment orchestration using ClusterPlan."""

from collections import defaultdict

from harness.remote_nodehost import RemoteNodehostClient


class Deployer:
    def __init__(self, remote_client, host_map):
        self.remote = remote_client
        self.host_map = dict(host_map)

    def nodes_by_host(self, cluster_plan):
        groups = defaultdict(list)
        for node in cluster_plan["nodes"]:
            groups[node["physical_host_id"]].append(node["node_id"])
        return {host_id: sorted(nodes) for host_id, nodes in sorted(groups.items())}

    def preflight(self):
        for host in sorted(self.host_map.values()):
            self.remote.nodehostctl(host, "status", "--json")

    def sync_package(self):
        for host in sorted(self.host_map.values()):
            self.remote.ssh.run(host, ("mkdir", "-p", "valkey-harness"))

    def start_virtual_az_runtime(self, run_id, cluster_plan):
        for host_id, node_ids in self.nodes_by_host(cluster_plan).items():
            self.remote.start(self.host_map[host_id], run_id, node_ids)

    def collect_artifacts(self, run_id):
        for host in sorted(self.host_map.values()):
            self.remote.collect(host, run_id)

    def cleanup(self, run_id):
        for host in sorted(self.host_map.values()):
            self.remote.cleanup(host, run_id)

    def deploy(self, run_id, cluster_plan):
        self.preflight()
        self.sync_package()
        self.start_virtual_az_runtime(run_id, cluster_plan)
        self.collect_artifacts(run_id)
        self.cleanup(run_id)
        return {"status": "OK", "hosts": sorted(self.host_map.values())}
