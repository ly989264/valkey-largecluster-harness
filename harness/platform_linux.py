"""Linux platform adapter."""

from harness.platform_adapter import PlatformAdapter
from harness.network_faults import NetworkFaultBackend, NetworkFaultResult


class LinuxPlatformAdapter(PlatformAdapter):
    name = "linux"

    def process_exists(self, pid):
        if self.executor is None:
            return False
        result = self.executor.run(("ps", "-p", str(pid)))
        return result.exit_code == 0

    def read_process_rss(self, pid):
        if self.executor is None:
            return None
        result = self.executor.run(("ps", "-o", "rss=", "-p", str(pid)))
        if result.exit_code != 0 or not result.stdout.strip():
            return None
        return int(result.stdout.strip().splitlines()[-1])

    def count_process_fds(self, pid):
        if self.executor is None:
            return None
        result = self.executor.run(("sh", "-c", f"ls /proc/{int(pid)}/fd | wc -l"))
        if result.exit_code != 0 or not result.stdout.strip():
            return None
        return int(result.stdout.strip())

    def list_sockets(self, pid=None):
        if self.executor is None:
            return []
        cmd = ("ss", "-tanp") if pid is None else ("ss", "-tanp")
        result = self.executor.run(cmd)
        if result.exit_code != 0:
            return []
        needle = "" if pid is None else f"pid={int(pid)},"
        return [line for line in result.stdout.splitlines() if not needle or needle in line]

    def supports_host_network(self):
        return True

    def supports_network_fault_injection(self):
        return True

    def network_fault_backend_hint(self):
        return "linux-tc-netem"

    def network_fault_backend(self, interface="lo", executor=None):
        return LinuxNetemBackend(interface=interface, executor=executor or self.executor)


class LinuxNetemBackend(NetworkFaultBackend):
    name = "linux-tc-netem"

    def __init__(self, interface="lo", executor=None):
        self.interface = interface
        self.executor = executor

    def capability(self):
        return NetworkFaultResult(
            status="OK",
            evidence=f"command construction for tc/netem on {self.interface}",
        )

    def isolate(self, targets):
        return self._planned("isolate", self._firewall_commands("-A", targets))

    def heal(self, targets):
        return self._planned("heal", self._firewall_commands("-D", targets))

    def delay(self, targets, milliseconds):
        commands = (
            ("tc", "qdisc", "replace", "dev", self.interface, "root", "netem", "delay", f"{int(milliseconds)}ms"),
        )
        return self._planned("delay", commands)

    def loss(self, targets, percent):
        commands = (
            ("tc", "qdisc", "replace", "dev", self.interface, "root", "netem", "loss", f"{float(percent):g}%"),
        )
        return self._planned("loss", commands)

    def clear(self, targets):
        commands = (("tc", "qdisc", "del", "dev", self.interface, "root"),)
        return self._planned("clear", commands)

    def _planned(self, action, commands):
        return NetworkFaultResult(status="OK", evidence=f"{action} command plan", commands=tuple(commands))

    def _firewall_commands(self, op, targets):
        commands = []
        for target in targets:
            for port in target.all_ports():
                commands.append(("iptables", op, "OUTPUT", "-p", "tcp", "--dport", str(port), "-j", "DROP"))
                commands.append(("iptables", op, "INPUT", "-p", "tcp", "--sport", str(port), "-j", "DROP"))
        return tuple(commands)
