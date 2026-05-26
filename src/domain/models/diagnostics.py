"""Typed diagnostic result models for troubleshooting execution."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union


@dataclass
class DiagnosticsResult:
    """Normalized diagnostics payload for one subsystem."""

    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def with_entry(self, key: str, value: Any) -> None:
        """Add a diagnostic entry."""
        self.data[key] = value

    def with_error(self, error: Union[Exception, str]) -> None:
        """Record an error without discarding existing entries."""
        self.error = str(error)
        self.data["error"] = self.error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to backward-compatible dictionary shape."""
        return dict(self.data)
