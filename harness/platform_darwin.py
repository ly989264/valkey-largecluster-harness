"""Darwin platform adapter."""

from harness.platform_adapter import PlatformAdapter


class DarwinPlatformAdapter(PlatformAdapter):
    name = "darwin"

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
        result = self.executor.run(("lsof", "-p", str(pid)))
        if result.exit_code != 0:
            return None
        return max(0, len([line for line in result.stdout.splitlines() if line.strip()]) - 1)

    def list_sockets(self, pid=None):
        if self.executor is None:
            return []
        cmd = ("lsof", "-nP", "-iTCP") if pid is None else ("lsof", "-nP", "-iTCP", "-p", str(pid))
        result = self.executor.run(cmd)
        if result.exit_code != 0:
            return []
        return [line for line in result.stdout.splitlines()[1:] if line.strip()]

    def supports_host_network(self):
        return True

    def supports_network_fault_injection(self):
        return False

    def network_fault_backend_hint(self):
        return "darwin-unsupported-use-linux-tc-netem"
