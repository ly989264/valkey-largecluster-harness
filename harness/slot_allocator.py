"""Valkey cluster hash slot allocation."""


TOTAL_SLOTS = 16384


class SlotAllocationError(ValueError):
    pass


def allocate_slots(primary_count):
    if primary_count <= 0:
        raise SlotAllocationError("primary_count must be > 0")
    base = TOTAL_SLOTS // primary_count
    extra = TOTAL_SLOTS % primary_count
    start = 0
    ranges = []
    for idx in range(primary_count):
        size = base + (1 if idx < extra else 0)
        end = start + size - 1
        ranges.append({"start": start, "end": end})
        start = end + 1
    if ranges[0]["start"] != 0 or ranges[-1]["end"] != TOTAL_SLOTS - 1:
        raise SlotAllocationError("slot ranges must cover 0..16383")
    for left, right in zip(ranges, ranges[1:]):
        if left["end"] + 1 != right["start"]:
            raise SlotAllocationError("slot ranges must be contiguous")
    return ranges
