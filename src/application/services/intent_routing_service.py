"""Intent classification service for fast-path troubleshooting."""

from typing import Callable, Optional

from ...intent_classifier import Intent


class IntentRoutingService:
    """Classify queries and optionally execute fast-path troubleshooting."""

    def __init__(
        self,
        *,
        classify_intent: Callable[[str], Intent],
        should_use_fast_path: Callable[[Intent], bool],
        execute_fast_path: Callable[[str, Intent], str],
        verbose: bool = False,
        print_intent_details: Optional[Callable[[Intent], None]] = None,
    ):
        self.classify_intent = classify_intent
        self.should_use_fast_path = should_use_fast_path
        self.execute_fast_path = execute_fast_path
        self.verbose = verbose
        self.print_intent_details = print_intent_details

    def try_fast_path(self, query: str) -> Optional[str]:
        """Return fast-path response when intent confidence is high enough."""
        intent = self.classify_intent(query)

        if self.verbose and self.print_intent_details:
            self.print_intent_details(intent)

        if self.should_use_fast_path(intent):
            return self.execute_fast_path(query, intent)

        return None
