"""Docker host-network nodehost contract."""

import shutil
from collections import defaultdict


class DockerCapability:
    def __init__(self, docker_cli=None, host_network=True):
        self.docker_cli = docker_cli if docker_cli is not None else shutil.which("docker")
        self.host_network = host_network

    def check(self):
        if not self.docker_cli:
            return {"status": "SKIPPED_RESOURCE", "reason": "docker CLI not found"}
        if not self.host_network:
            return {"status": "SKIPPED_RESOURCE", "reason": "host network mode unavailable"}
        return {"status": "PASS", "docker_cli": self.docker_cli}


class DockerNodehostClient:
    def __init__(self, image="valkey-nodehost:local", docker_cli="docker"):
        self.image = image
        self.docker_cli = docker_cli

    def group_nodes_by_virtual_az(self, cluster_plan):
        groups = defaultdict(list)
        for node in cluster_plan["nodes"]:
            groups[node["virtual_az_id"]].append(node["node_id"])
        return {az: sorted(nodes) for az, nodes in sorted(groups.items())}

    def build_run_commands(self, cluster_plan, run_id):
        commands = []
        for virtual_az_id, node_ids in self.group_nodes_by_virtual_az(cluster_plan).items():
            commands.append(
                [
                    self.docker_cli,
                    "run",
                    "--rm",
                    "--network",
                    "host",
                    "--name",
                    f"vlc-{run_id}-{virtual_az_id}",
                    "-e",
                    f"RUN_ID={run_id}",
                    "-e",
                    f"VIRTUAL_AZ_ID={virtual_az_id}",
                    "-e",
                    "NODE_IDS=" + ",".join(node_ids),
                    self.image,
                    "status",
                    "--json",
                ]
            )
        return commands
