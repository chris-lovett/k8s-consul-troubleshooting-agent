"""Centralized application settings and config merge logic."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AppSettings:
    """Runtime settings after CLI and config merge."""

    setup: bool
    model: str
    reasoning_model: Optional[str]
    namespace: str
    consul_host: str
    consul_port: int
    verbose: bool
    query: Optional[str]
    enable_memory: bool
    enable_intent_routing: bool
    enable_cache: bool
    no_health_check: bool
    cache_ttl: int
    cache_size: int
    max_iterations: int
    max_time: int

    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_NAMESPACE = "default"
    DEFAULT_CONSUL_HOST = "localhost"
    DEFAULT_CONSUL_PORT = 8500
    DEFAULT_CACHE_TTL = 300
    DEFAULT_CACHE_SIZE = 100
    DEFAULT_MAX_ITERATIONS = 35
    DEFAULT_MAX_TIME = 300

    @classmethod
    def from_sources(cls, args: Any, saved_config: Optional[Dict[str, Any]]) -> "AppSettings":
        """Build settings from parsed CLI args and optional saved YAML config."""
        model = args.model
        namespace = args.namespace
        consul_host = args.consul_host
        consul_port = args.consul_port
        cache_ttl = args.cache_ttl
        cache_size = args.cache_size
        max_iterations = args.max_iterations
        max_time = args.max_time

        enable_memory = not args.no_memory
        enable_cache = not args.no_cache
        enable_intent_routing = not args.no_intent_routing

        if saved_config:
            if model is None and "model" in saved_config:
                model = saved_config["model"]
            if namespace is None and "kubernetes_namespace" in saved_config:
                namespace = saved_config["kubernetes_namespace"]
            if consul_host is None and "consul_host" in saved_config:
                consul_host = saved_config["consul_host"]
            if consul_port is None and "consul_port" in saved_config:
                consul_port = saved_config["consul_port"]

            if cache_ttl is None and "cache_ttl" in saved_config:
                cache_ttl = saved_config["cache_ttl"]
            if cache_size is None and "cache_size" in saved_config:
                cache_size = saved_config["cache_size"]
            if max_iterations is None and "max_iterations" in saved_config:
                max_iterations = saved_config["max_iterations"]
            if max_time is None and "max_execution_time" in saved_config:
                max_time = saved_config["max_execution_time"]

            # CLI disable flags have highest precedence.
            if not args.no_memory and "enable_memory" in saved_config:
                enable_memory = bool(saved_config["enable_memory"])
            if not args.no_cache and "enable_cache" in saved_config:
                enable_cache = bool(saved_config["enable_cache"])
            if not args.no_intent_routing and "enable_intent_routing" in saved_config:
                enable_intent_routing = bool(saved_config["enable_intent_routing"])

        return cls(
            setup=bool(args.setup),
            model=model or cls.DEFAULT_MODEL,
            reasoning_model=args.reasoning_model,
            namespace=namespace or cls.DEFAULT_NAMESPACE,
            consul_host=consul_host or cls.DEFAULT_CONSUL_HOST,
            consul_port=int(consul_port or cls.DEFAULT_CONSUL_PORT),
            verbose=bool(args.verbose),
            query=args.query,
            enable_memory=enable_memory,
            enable_intent_routing=enable_intent_routing,
            enable_cache=enable_cache,
            no_health_check=bool(args.no_health_check),
            cache_ttl=int(cache_ttl or cls.DEFAULT_CACHE_TTL),
            cache_size=int(cache_size or cls.DEFAULT_CACHE_SIZE),
            max_iterations=int(max_iterations or cls.DEFAULT_MAX_ITERATIONS),
            max_time=int(max_time or cls.DEFAULT_MAX_TIME),
        )
