from __future__ import annotations

from harness.cluster.clusterscan import run_clusterscan_matrix


class FakeClusterScanClient:
    def __init__(self, slot_supported: bool = True) -> None:
        self.slot_supported = slot_supported

    def command(self, host: str, port: int, *args: str) -> str:
        if args[:2] == ("COMMAND", "INFO"):
            return "supported"
        if "SLOT" in args and not self.slot_supported:
            raise RuntimeError("ERR syntax")
        return "0 key-count=0"


def test_clusterscan_matrix_covers_cursor_match_type_and_slot() -> None:
    result = run_clusterscan_matrix(FakeClusterScanClient(), ("127.0.0.1", 7000))

    assert result.status == "VALIDATED"
    assert set(result.checks) == {"cursor", "match", "type", "slot"}


def test_clusterscan_unsupported_slot_is_skipped_scope() -> None:
    result = run_clusterscan_matrix(FakeClusterScanClient(slot_supported=False), ("127.0.0.1", 7000))

    assert result.status == "VALIDATED"
    assert result.checks["slot"] == "SKIPPED_SCOPE"
