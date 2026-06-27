"""Remote nodehost client over SSH."""


class RemoteNodehostClient:
    def __init__(self, ssh_executor, python="python3"):
        self.ssh = ssh_executor
        self.python = python

    def nodehostctl(self, host, *args):
        return self.ssh.run(host, (self.python, "-m", "nodehost.nodehostctl", *args))

    def status(self, host, run_id):
        return self.nodehostctl(host, "status", "--run-id", run_id, "--json")

    def start(self, host, run_id, node_ids):
        argv = ["start", "--run-id", run_id]
        for node_id in node_ids:
            argv.extend(["--node-id", node_id])
        argv.append("--json")
        return self.nodehostctl(host, *argv)

    def cleanup(self, host, run_id):
        return self.nodehostctl(host, "cleanup", "--run-id", run_id, "--json")

    def collect(self, host, run_id):
        return self.ssh.run(host, ("tar", "cf", "-", f"nodehost-artifacts/{run_id}"))
