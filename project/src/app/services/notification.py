from __future__ import annotations

from app.services.notification_orchestrator import NotificationOrchestrator


class NotificationService:
    """Backward-compatible entrypoint — delegates to orchestrator."""

    def __init__(self, session) -> None:
        self._orchestrator = NotificationOrchestrator(session)

    def send_for_match(self, match_id: int) -> bool:
        result = self._orchestrator.orchestrate(match_id)
        return result["sent"] > 0 or result["skipped"] > 0
