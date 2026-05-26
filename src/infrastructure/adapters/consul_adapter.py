"""Consul adapter wrapping ConsulTools."""

from typing import Optional

from ...tools.consul_tools import ConsulTools


class ConsulAdapter:
    """Infrastructure adapter for Consul diagnostics access."""

    def __init__(self, tools: ConsulTools):
        self._tools = tools

    def list_services(self, datacenter: Optional[str] = None) -> str:
        return self._tools.list_services(datacenter)

    def get_service_health(self, service_name: str, datacenter: Optional[str] = None) -> str:
        return self._tools.get_service_health(service_name, datacenter)

    def get_service_instances(self, service_name: str, datacenter: Optional[str] = None) -> str:
        return self._tools.get_service_instances(service_name, datacenter)

    def list_intentions(self) -> str:
        return self._tools.list_intentions()

    def check_intention(self, source_service: str, destination_service: str) -> str:
        return self._tools.check_intention(source_service, destination_service)

    def get_agent_members(self) -> str:
        return self._tools.get_agent_members()
