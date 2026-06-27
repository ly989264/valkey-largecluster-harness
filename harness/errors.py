"""Shared error types for harnessctl."""


class HarnessError(Exception):
    """Base error that can be rendered as structured JSON."""

    def __init__(self, reason, *, status="ERROR", exit_code=1):
        super().__init__(reason)
        self.reason = reason
        self.status = status
        self.exit_code = exit_code
