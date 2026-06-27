"""Virtual AZ topology model for P03 planning."""

from dataclasses import dataclass


@dataclass(frozen=True)
class VirtualAZPlacement:
    virtual_az_id: str
    physical_host_id: str
    weight: int = 1

    def validate(self):
        if not self.virtual_az_id:
            raise ValueError("virtual_az_id is required")
        if not self.physical_host_id:
            raise ValueError("physical_host_id is required")
        if self.weight <= 0:
            raise ValueError("weight must be > 0")

    def sort_key(self):
        return (self.physical_host_id, self.virtual_az_id)

    def to_dict(self):
        return {"physical_host_id": self.physical_host_id, "virtual_az_id": self.virtual_az_id, "weight": self.weight}


def build_matrix(placements, physical_host_ids, virtual_az_ids, *, full=False):
    by_pair = {(p.physical_host_id, p.virtual_az_id): p.weight for p in placements}
    rows = []
    for host_id in sorted(physical_host_ids):
        for az_id in sorted(virtual_az_ids):
            if full or (host_id, az_id) in by_pair:
                rows.append(
                    {
                        "physical_host_id": host_id,
                        "virtual_az_id": az_id,
                        "weight": by_pair.get((host_id, az_id), 0),
                    }
                )
    return rows
