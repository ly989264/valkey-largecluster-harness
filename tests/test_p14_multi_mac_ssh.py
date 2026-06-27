import unittest

from harness.deployer import Deployer
from harness.planner import build_cluster_plan
from harness.remote_nodehost import RemoteNodehostClient
from harness.ssh_exec import FakeSSHExecutor


def plan():
    return build_cluster_plan("inventories/two-mac-physical-aligned.yaml", "scenarios/smoke-6.yaml")["cluster_plan"]


class MultiMacSSHP14Test(unittest.TestCase):
    def test_fake_ssh_verifies_exact_host_targeting(self):
        fake = FakeSSHExecutor()
        remote = RemoteNodehostClient(fake)
        Deployer(remote, {"mac-1": "host-a", "mac-2": "host-b"}).deploy("run", plan())
        hosts = [cmd.host for cmd in fake.commands]
        self.assertIn("host-a", hosts)
        self.assertIn("host-b", hosts)
        start_commands = [cmd for cmd in fake.commands if "start" in cmd.argv]
        self.assertEqual(len(start_commands), 2)
        self.assertTrue(any("--node-id" in cmd.argv for cmd in start_commands))

    def test_remote_orchestration_reads_cluster_plan_not_planner(self):
        deployer = Deployer(RemoteNodehostClient(FakeSSHExecutor()), {"mac-1": "host-a", "mac-2": "host-b"})
        grouped = deployer.nodes_by_host(plan())
        self.assertEqual(set(grouped), {"mac-1", "mac-2"})
        self.assertTrue(all(node.startswith("node-") for nodes in grouped.values() for node in nodes))

    def test_real_ssh_absence_does_not_affect_unit_tests(self):
        fake = FakeSSHExecutor()
        RemoteNodehostClient(fake).status("host-a", "run")
        self.assertEqual(fake.commands[0].host, "host-a")
        self.assertIn("BatchMode", "BatchMode=yes")


if __name__ == "__main__":
    unittest.main()
