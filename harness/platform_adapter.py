"""Platform adapter interface and factory."""

import socket
import sys


class PlatformAdapter:
    name = "generic"

    def __init__(self, executor=None):
        self.executor = executor

    def detect_platform(self):
        return self.name

    def check_port_available(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("", int(port)))
            except OSError:
                return False
        return True

    def process_exists(self, pid):
        return False

    def read_process_rss(self, pid):
        return None

    def count_process_fds(self, pid):
        return None

    def list_sockets(self, pid=None):
        return []

    def supports_host_network(self):
        return False

    def supports_network_fault_injection(self):
        return False

    def network_fault_backend_hint(self):
        return "unsupported"

    def capabilities(self):
        return {
            "platform": self.detect_platform(),
            "host_network": self.supports_host_network(),
            "network_fault_injection": self.supports_network_fault_injection(),
            "network_fault_backend_hint": self.network_fault_backend_hint(),
        }


def adapter_for_platform(platform_name=None, executor=None):
    name = platform_name or sys.platform
    if name.startswith("darwin"):
        from harness.platform_darwin import DarwinPlatformAdapter

        return DarwinPlatformAdapter(executor=executor)
    if name.startswith("linux"):
        from harness.platform_linux import LinuxPlatformAdapter

        return LinuxPlatformAdapter(executor=executor)
    return PlatformAdapter(executor=executor)
