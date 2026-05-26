"""LLM and executor construction for troubleshooting runtime."""

from typing import Optional

from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from ...prompts.system_prompts import SYSTEM_PROMPT, REACT_PROMPT_TEMPLATE


class LLMRuntimeService:
    """Build runtime ReAct agents and executors for different LLMs."""

    def __init__(
        self,
        *,
        tools,
        memory: Optional[ConversationBufferMemory],
        verbose: bool,
        max_iterations: int,
        max_execution_time: int,
    ):
        self.tools = tools
        self.memory = memory
        self.verbose = verbose
        self.max_iterations = max_iterations
        self.max_execution_time = max_execution_time
        self._prompt = PromptTemplate.from_template(SYSTEM_PROMPT + "\n\n" + REACT_PROMPT_TEMPLATE)

    def create_react_agent(self, llm: ChatOpenAI):
        """Create a ReAct agent for the provided LLM."""
        return create_react_agent(
            llm=llm,
            tools=self.tools,
            prompt=self._prompt,
        )

    def create_executor(self, llm: ChatOpenAI) -> AgentExecutor:
        """Create an AgentExecutor using a ReAct agent for the provided LLM."""
        agent = self.create_react_agent(llm)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=self.verbose,
            max_iterations=self.max_iterations,
            max_execution_time=self.max_execution_time,
            handle_parsing_errors=True,
        )
