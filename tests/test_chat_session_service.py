"""Tests for ChatSessionService command handling."""

from unittest.mock import Mock

from src.application.services import ChatSessionService


def _build_service():
    return ChatSessionService(
        enable_memory=True,
        enable_intent_routing=True,
        enable_cache=True,
        enable_workflow=True,
        workflow_available=True,
        clear_memory=Mock(),
        get_conversation_history=Mock(return_value=[]),
        get_conversation_summary=Mock(return_value="summary"),
        get_cache_stats=Mock(return_value="cache stats"),
        clear_cache=Mock(),
        run_with_spinner=Mock(return_value="ok"),
    )


def test_chat_session_service_handles_clear_command():
    service = _build_service()

    handled = service._handle_command("/clear")

    assert handled is True
    service.clear_memory.assert_called_once()


def test_chat_session_service_handles_unknown_command():
    service = _build_service()

    handled = service._handle_command("/doesnotexist")

    assert handled is True
