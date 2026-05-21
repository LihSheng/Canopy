from unittest.mock import MagicMock

from cache.cache_store import CacheStore
from cache.config_cache import ConfigCache
from cache.invalidation import CacheInvalidator
from cache.routing_cache import RoutingCache


class TestCacheStore:
    def test_get_set_basic(self):
        store = CacheStore()
        store.set("key1", "value1")
        assert store.get("key1") == "value1"

    def test_get_returns_none_for_missing_key(self):
        store = CacheStore()
        assert store.get("nonexistent") is None

    def test_get_returns_none_for_expired_entry(self):
        store = CacheStore(default_ttl_seconds=60)
        store.set("key1", "value1", ttl_seconds=-1)
        assert store.get("key1") is None

    def test_delete_removes_key(self):
        store = CacheStore()
        store.set("key1", "value1")
        store.delete("key1")
        assert store.get("key1") is None

    def test_delete_by_prefix_removes_matching_keys(self):
        store = CacheStore()
        store.set("ns:a:1", "v1")
        store.set("ns:a:2", "v2")
        store.set("ns:b:1", "v3")
        store.set("other:1", "v4")

        count = store.delete_by_prefix("ns:")
        assert count == 3
        assert store.get("ns:a:1") is None
        assert store.get("ns:a:2") is None
        assert store.get("ns:b:1") is None
        assert store.get("other:1") == "v4"

    def test_delete_by_prefix_returns_zero_for_no_match(self):
        store = CacheStore()
        count = store.delete_by_prefix("no-match:")
        assert count == 0

    def test_clear_removes_all(self):
        store = CacheStore()
        store.set("a", 1)
        store.set("b", 2)
        store.set("c", 3)
        store.clear()
        assert store.get("a") is None
        assert store.get("b") is None
        assert store.get("c") is None

    def test_cleanup_expired_removes_only_expired(self):
        store = CacheStore()
        store.set("fresh", "keep", ttl_seconds=999)
        store.set("stale", "remove", ttl_seconds=-1)
        count = store._cleanup_expired()
        assert count == 1
        assert store.get("fresh") == "keep"
        assert store.get("stale") is None

    def test_cleanup_expired_returns_zero_for_all_fresh(self):
        store = CacheStore()
        store.set("a", 1, ttl_seconds=999)
        store.set("b", 2, ttl_seconds=999)
        count = store._cleanup_expired()
        assert count == 0

    def test_different_data_types(self):
        store = CacheStore()
        store.set("int", 42)
        store.set("list", [1, 2, 3])
        store.set("dict", {"a": 1})
        store.set("none", None)
        assert store.get("int") == 42
        assert store.get("list") == [1, 2, 3]
        assert store.get("dict") == {"a": 1}
        assert store.get("none") is None

    def test_default_ttl_is_used_when_not_specified(self):
        store = CacheStore(default_ttl_seconds=999)
        store.set("key", "value")
        assert store.get("key") == "value"


class TestRoutingCache:
    def test_get_tenant_database_target_from_cache(self):
        store = CacheStore()
        db_factory = MagicMock()
        routing = RoutingCache(store, db_factory)

        routing.cache_tenant_database_target(
            "tenant-a",
            {"database_kind": "tenant_data", "connection_ref": "pg://a", "tenant_id": "tenant-a"},
        )

        result = routing.get_tenant_database_target("tenant-a")
        assert result["database_kind"] == "tenant_data"
        assert result["connection_ref"] == "pg://a"
        db_factory.assert_not_called()

    def test_get_tenant_database_target_falls_back_to_db(self):
        class MockSession:
            def close(self):
                pass

            def query(self, model):
                class MockQuery:
                    def filter(self, *args):
                        return self

                    def first(self):
                        return type(
                            "FakeTarget",
                            (),
                            {
                                "database_kind": "tenant_data",
                                "connection_ref": "pg://db",
                                "tenant_id": "tenant-a",
                            },
                        )()

                return MockQuery()

        store = CacheStore()
        db_factory = MagicMock(return_value=MockSession())
        routing = RoutingCache(store, db_factory)

        result = routing.get_tenant_database_target("tenant-a")
        assert result["database_kind"] == "tenant_data"
        assert result["connection_ref"] == "pg://db"

        cached = routing.get_tenant_database_target("tenant-a")
        assert cached["database_kind"] == "tenant_data"

    def test_get_tenant_database_target_returns_none_when_not_found(self):
        class MockSession:
            def close(self):
                pass

            def query(self, model):
                class MockQuery:
                    def filter(self, *args):
                        return self

                    def first(self):
                        return None

                return MockQuery()

        store = CacheStore()
        db_factory = MagicMock(return_value=MockSession())
        routing = RoutingCache(store, db_factory)

        result = routing.get_tenant_database_target("tenant-none")
        assert result is None

    def test_invalidate_tenant_removes_cache(self):
        store = CacheStore()
        db_factory = MagicMock()
        routing = RoutingCache(store, db_factory)

        routing.cache_tenant_database_target(
            "tenant-a", {"database_kind": "k", "connection_ref": "r", "tenant_id": "id"}
        )
        routing.invalidate_tenant("tenant-a")
        assert store.get("routing:tenant-a") is None

    def test_invalidate_all_removes_all_routing_caches(self):
        store = CacheStore()
        db_factory = MagicMock()
        routing = RoutingCache(store, db_factory)

        routing.cache_tenant_database_target("tenant-a", {})
        routing.cache_tenant_database_target("tenant-b", {})
        routing.invalidate_all()
        assert store.get("routing:tenant-a") is None
        assert store.get("routing:tenant-b") is None


class TestConfigCache:
    def test_get_tenant_config_from_cache(self):
        store = CacheStore()
        config_cache = ConfigCache(store)

        config_cache.cache_tenant_config("tenant-a", "storage_limit", "10GB", ttl_seconds=120)
        value = config_cache.get_tenant_config("tenant-a", "storage_limit")
        assert value == "10GB"

    def test_get_tenant_config_falls_back_to_repo(self):
        class FakeConfig:
            config_value_json = '{"max":100}'

        class MockRepo:
            def get_config(self, tenant_id, key):
                return FakeConfig()

        store = CacheStore()
        config_cache = ConfigCache(store, config_repository=MockRepo())

        value = config_cache.get_tenant_config("tenant-a", "some_key")
        assert value == '{"max":100}'

    def test_get_tenant_config_returns_none_for_missing(self):
        class MockRepo:
            def get_config(self, tenant_id, key):
                return None

        store = CacheStore()
        config_cache = ConfigCache(store, config_repository=MockRepo())

        value = config_cache.get_tenant_config("tenant-a", "nonexistent")
        assert value is None

    def test_invalidate_tenant_removes_all_configs(self):
        store = CacheStore()
        config_cache = ConfigCache(store)

        config_cache.cache_tenant_config("tenant-a", "k1", "v1")
        config_cache.cache_tenant_config("tenant-a", "k2", "v2")
        config_cache.cache_tenant_config("tenant-b", "k1", "v3")

        config_cache.invalidate_tenant("tenant-a")
        assert config_cache.get_tenant_config("tenant-a", "k1") is None
        assert config_cache.get_tenant_config("tenant-a", "k2") is None
        assert config_cache.get_tenant_config("tenant-b", "k1") == "v3"

    def test_invalidate_config_removes_single_key(self):
        store = CacheStore()
        config_cache = ConfigCache(store)

        config_cache.cache_tenant_config("tenant-a", "k1", "v1")
        config_cache.cache_tenant_config("tenant-a", "k2", "v2")

        config_cache.invalidate_config("tenant-a", "k1")
        assert config_cache.get_tenant_config("tenant-a", "k1") is None
        assert config_cache.get_tenant_config("tenant-a", "k2") == "v2"

    def test_invalidate_all_removes_all_configs(self):
        store = CacheStore()
        config_cache = ConfigCache(store)

        config_cache.cache_tenant_config("tenant-a", "k1", "v1")
        config_cache.cache_tenant_config("tenant-b", "k2", "v2")
        config_cache.invalidate_all()
        assert config_cache.get_tenant_config("tenant-a", "k1") is None
        assert config_cache.get_tenant_config("tenant-b", "k2") is None


class TestCacheInvalidator:
    def test_on_tenant_provisioned_invalidates_routing(self):
        store = CacheStore()
        routing = RoutingCache(store, MagicMock())
        config = ConfigCache(store)
        invalidator = CacheInvalidator(routing, config)

        routing.cache_tenant_database_target("tenant-a", {"x": "y"})
        invalidator.on_tenant_provisioned("tenant-a")
        assert store.get("routing:tenant-a") is None

    def test_on_tenant_suspended_invalidates_routing(self):
        store = CacheStore()
        routing = RoutingCache(store, MagicMock())
        config = ConfigCache(store)
        invalidator = CacheInvalidator(routing, config)

        routing.cache_tenant_database_target("tenant-a", {"x": "y"})
        invalidator.on_tenant_suspended("tenant-a")
        assert store.get("routing:tenant-a") is None

    def test_on_tenant_restored_invalidates_routing(self):
        store = CacheStore()
        routing = RoutingCache(store, MagicMock())
        config = ConfigCache(store)
        invalidator = CacheInvalidator(routing, config)

        routing.cache_tenant_database_target("tenant-a", {"x": "y"})
        invalidator.on_tenant_restored("tenant-a")
        assert store.get("routing:tenant-a") is None

    def test_on_tenant_config_changed_invalidates_specific_key(self):
        store = CacheStore()
        routing = RoutingCache(store, MagicMock())
        config = ConfigCache(store)
        invalidator = CacheInvalidator(routing, config)

        config.cache_tenant_config("tenant-a", "k1", "v1")
        config.cache_tenant_config("tenant-a", "k2", "v2")
        invalidator.on_tenant_config_changed("tenant-a", "k1")
        assert config.get_tenant_config("tenant-a", "k1") is None
        assert config.get_tenant_config("tenant-a", "k2") == "v2"

    def test_on_tenant_config_changed_invalidates_all_for_tenant(self):
        store = CacheStore()
        routing = RoutingCache(store, MagicMock())
        config = ConfigCache(store)
        invalidator = CacheInvalidator(routing, config)

        config.cache_tenant_config("tenant-a", "k1", "v1")
        config.cache_tenant_config("tenant-a", "k2", "v2")
        invalidator.on_tenant_config_changed("tenant-a")
        assert config.get_tenant_config("tenant-a", "k1") is None
        assert config.get_tenant_config("tenant-a", "k2") is None

    def test_on_database_rotation_invalidates_routing(self):
        store = CacheStore()
        routing = RoutingCache(store, MagicMock())
        config = ConfigCache(store)
        invalidator = CacheInvalidator(routing, config)

        routing.cache_tenant_database_target("tenant-a", {"x": "y"})
        invalidator.on_database_rotation("tenant-a", "old-ref", "new-ref")
        assert store.get("routing:tenant-a") is None

    def test_on_schema_rollout_invalidates_all_routing(self):
        store = CacheStore()
        routing = RoutingCache(store, MagicMock())
        config = ConfigCache(store)
        invalidator = CacheInvalidator(routing, config)

        routing.cache_tenant_database_target("tenant-a", {"x": "y"})
        routing.cache_tenant_database_target("tenant-b", {"x": "z"})
        invalidator.on_schema_rollout()
        assert store.get("routing:tenant-a") is None
        assert store.get("routing:tenant-b") is None
