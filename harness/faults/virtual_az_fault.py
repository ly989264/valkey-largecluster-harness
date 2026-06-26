from __future__ import annotations

from dataclasses import dataclass

from harness.faults.process_fault import FaultResult, kill_process


@dataclass(frozen=True)
class VirtualAzFaultResult:
    virtual_az_id: str
    process_results: list[FaultResult]


def kill_virtual_az(processes: list[dict], virtual_az_id: str, apply: bool = False) -> VirtualAzFaultResult:
    results = []
    for process in processes:
        if process.get("virtual_az_id") == virtual_az_id:
            results.append(kill_process(int(process["pid"]), apply=apply))
    return VirtualAzFaultResult(virtual_az_id=virtual_az_id, process_results=results)
