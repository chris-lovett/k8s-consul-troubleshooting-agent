"""Typed remediation models for troubleshooting results."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class AutomatedFix:
    """Suggested automatable remediation action."""

    pattern: str
    fix_type: str
    description: str
    safe: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to backward-compatible dictionary shape."""
        return {
            "pattern": self.pattern,
            "fix_type": self.fix_type,
            "description": self.description,
            "safe": self.safe,
        }


@dataclass
class RemediationPlan:
    """Root-cause remediation details and optional automation suggestions."""

    root_cause: str = ""
    remediation_steps: List[str] = field(default_factory=list)
    automated_fixes: List[AutomatedFix] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def add_step(self, step: str) -> None:
        """Append one remediation step."""
        if step:
            self.remediation_steps.append(step)

    def add_automated_fix(self, fix: AutomatedFix) -> None:
        """Append one automated fix suggestion."""
        self.automated_fixes.append(fix)

    def automated_fixes_as_dicts(self) -> List[Dict[str, Any]]:
        """Convert automated fixes to legacy list[dict] format."""
        return [fix.to_dict() for fix in self.automated_fixes]
