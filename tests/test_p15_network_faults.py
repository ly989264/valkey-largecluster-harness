import unittest

from harness.faults import NetworkFaultExecutor, NetworkFaultPlan
from harness.network_faults import UnsupportedNetworkFaultBackend, targets_for_virtual_az
from harness.planner import build_cluster_plan
from harness.platform_darwin import DarwinPlatformAdapter
from harness.platform_linux import LinuxNetemBackend, LinuxPlatformAdapter
from nodehost.faults_network import plan_network_fault


def cluster_plan():
    return build_cluster_plan("inventories/two-mac-physical-aligned.yaml", "scenarios/smoke-6.yaml")["cluster_plan"]


class NetworkFaultP15Test(unittest.TestCase):
    def test_unsupported_environment_returns_skipped_resource(self):
        backend = UnsupportedNetworkFaultBackend("no privileged network backend", "unit test")
        result = backend.isolate(targets_for_virtual_az(cluster_plan(), "az-1")).to_dict()
        self.assertEqual(result["status"], "SKIPPED_RESOURCE")
        self.assertIn("no privileged", result["reason"])
        darwin = DarwinPlatformAdapter()
        self.assertFalse(darwin.supports_network_fault_injection())
        self.assertEqual(darwin.network_fault_backend().capability().status, "SKIPPED_RESOURCE")

    def test_linux_command_plan_targets_client_and_cluster_bus_ports(self):
        plan = cluster_plan()
        target = targets_for_virtual_az(plan, "az-1")[0]
        result = LinuxNetemBackend(interface="eth0").isolate((target,)).to_dict()
        flat = [" ".join(command) for command in result["commands"]]
        joined = "\n".join(flat)
        self.assertIn(str(target.client_port), joined)
        self.assertIn(str(target.bus_port), joined)
        self.assertGreaterEqual(len(result["commands"]), 4)

    def test_isolate_heal_delay_loss_clear_command_plans(self):
        target = targets_for_virtual_az(cluster_plan(), "az-1")[0]
        backend = LinuxPlatformAdapter().network_fault_backend(interface="eth1")
        isolate = backend.isolate((target,)).to_dict()
        heal = backend.heal((target,)).to_dict()
        delay = backend.delay((target,), 150).to_dict()
        loss = backend.loss((target,), 2.5).to_dict()
        clear = backend.clear((target,)).to_dict()
        self.assertTrue(all(command[1] == "-A" for command in isolate["commands"]))
        self.assertTrue(all(command[1] == "-D" for command in heal["commands"]))
        self.assertEqual(delay["commands"][0], ["tc", "qdisc", "replace", "dev", "eth1", "root", "netem", "delay", "150ms"])
        self.assertEqual(loss["commands"][0], ["tc", "qdisc", "replace", "dev", "eth1", "root", "netem", "loss", "2.5%"])
        self.assertEqual(clear["commands"][0], ["tc", "qdisc", "del", "dev", "eth1", "root"])

    def test_executor_and_nodehost_entry_use_cluster_plan_targets(self):
        plan = cluster_plan()
        backend = LinuxNetemBackend()
        executor = NetworkFaultExecutor(backend)
        executed = executor.execute(plan, NetworkFaultPlan(action="clear", virtual_az_id="az-1"))
        nodehost = plan_network_fault(plan, backend, "delay", "az-1", milliseconds=25)
        expected = [target.node_id for target in targets_for_virtual_az(plan, "az-1")]
        self.assertEqual(executed["targets"], expected)
        self.assertEqual(nodehost["commands"][0][-1], "25ms")


if __name__ == "__main__":
    unittest.main()
