import unittest

from harness.docker_nodehost import DockerCapability, DockerNodehostClient
from harness.planner import build_cluster_plan


def plan():
    return build_cluster_plan("inventories/three-mac-uniform-interleaved.yaml", "scenarios/scale-100.yaml")["cluster_plan"]


class DockerHostnetP13Test(unittest.TestCase):
    def test_run_commands_are_per_virtual_az_not_per_node(self):
        cluster_plan = plan()
        commands = DockerNodehostClient(image="img").build_run_commands(cluster_plan, "run")
        virtual_azs = {node["virtual_az_id"] for node in cluster_plan["nodes"]}
        self.assertEqual(len(commands), len(virtual_azs))
        self.assertLess(len(commands), len(cluster_plan["nodes"]))
        for command in commands:
            self.assertIn("--network", command)
            self.assertIn("host", command)
            self.assertTrue(any(part.startswith("NODE_IDS=") and "," in part for part in command))

    def test_no_forbidden_docker_dependencies_in_command(self):
        rendered = " ".join(" ".join(command) for command in DockerNodehostClient().build_run_commands(plan(), "run"))
        self.assertNotIn("docker" + ":dind", rendered)
        self.assertNotIn("DOCKER_HOST" + "=tcp://", rendered)
        self.assertNotIn("privileged", rendered)

    def test_unavailable_docker_returns_skipped_resource(self):
        self.assertEqual(DockerCapability(docker_cli="").check()["status"], "SKIPPED_RESOURCE")
        self.assertEqual(DockerCapability(docker_cli="docker", host_network=False).check()["status"], "SKIPPED_RESOURCE")


if __name__ == "__main__":
    unittest.main()
