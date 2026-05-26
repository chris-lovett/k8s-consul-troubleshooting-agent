"""Tests for LLMRuntimeService."""

from unittest.mock import Mock, patch

from src.application.services import LLMRuntimeService


@patch("src.application.services.llm_runtime_service.AgentExecutor")
@patch("src.application.services.llm_runtime_service.create_react_agent")
def test_llm_runtime_service_builds_executor(mock_create_react_agent, mock_executor):
    tools = [Mock(name="tool")]
    memory = Mock()
    llm = Mock()

    runtime = LLMRuntimeService(
        tools=tools,
        memory=memory,
        verbose=False,
        max_iterations=5,
        max_execution_time=60,
    )

    mock_create_react_agent.return_value = Mock(name="agent")
    mock_executor.return_value = Mock(name="executor")

    executor = runtime.create_executor(llm)

    assert executor is mock_executor.return_value
    mock_create_react_agent.assert_called_once()
    mock_executor.assert_called_once()
