"""Linux platform adapter."""

from harness.platform_adapter import PlatformAdapter


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
