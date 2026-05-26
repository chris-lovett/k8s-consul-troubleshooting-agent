"""Tests for core settings and routing services."""

from argparse import Namespace

from src.core.router import QueryRouter, RouteKind
from src.core.settings import AppSettings


def test_router_live_troubleshooting():
    router = QueryRouter()
    route = router.route("check pod web-api status")
    assert route == RouteKind.LIVE_TROUBLESHOOTING


def test_router_repo_code_assistance():
    router = QueryRouter()
    route = router.route("help me refactor this module")
    assert route == RouteKind.REPO_CODE_ASSISTANCE


def test_router_direct_answer_default():
    router = QueryRouter()
    route = router.route("summarize this")
    assert route == RouteKind.DIRECT_ANSWER


def test_settings_merge_with_saved_config():
    args = Namespace(
        setup=False,
        model=None,
        reasoning_model=None,
        namespace=None,
        consul_host=None,
        consul_port=None,
        verbose=False,
        query=None,
        no_memory=False,
        no_intent_routing=False,
        no_cache=False,
        no_health_check=False,
        cache_ttl=None,
        cache_size=None,
        max_iterations=None,
        max_time=None,
    )
    saved = {
        "model": "gpt-4o",
        "kubernetes_namespace": "prod",
        "consul_host": "consul.service",
        "consul_port": 9500,
        "cache_ttl": 111,
        "cache_size": 222,
        "max_iterations": 10,
        "max_execution_time": 55,
        "enable_memory": False,
        "enable_cache": False,
        "enable_intent_routing": True,
    }

    settings = AppSettings.from_sources(args=args, saved_config=saved)

    assert settings.model == "gpt-4o"
    assert settings.namespace == "prod"
    assert settings.consul_host == "consul.service"
    assert settings.consul_port == 9500
    assert settings.cache_ttl == 111
    assert settings.cache_size == 222
    assert settings.max_iterations == 10
    assert settings.max_time == 55
    assert settings.enable_memory is False
    assert settings.enable_cache is False
    assert settings.enable_intent_routing is True


def test_settings_cli_disable_overrides_saved_config():
    args = Namespace(
        setup=False,
        model=None,
        reasoning_model=None,
        namespace=None,
        consul_host=None,
        consul_port=None,
        verbose=False,
        query=None,
        no_memory=True,
        no_intent_routing=True,
        no_cache=True,
        no_health_check=False,
        cache_ttl=None,
        cache_size=None,
        max_iterations=None,
        max_time=None,
    )
    saved = {
        "enable_memory": True,
        "enable_cache": True,
        "enable_intent_routing": True,
    }

    settings = AppSettings.from_sources(args=args, saved_config=saved)

    assert settings.enable_memory is False
    assert settings.enable_cache is False
    assert settings.enable_intent_routing is False
