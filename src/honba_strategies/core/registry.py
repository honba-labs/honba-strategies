"""Strategy registry with decorator-based registration and factory methods."""

from __future__ import annotations

import importlib
import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.errors import StrategyNotFoundError


@dataclass
class StrategyMetadata:
    """Metadata for a registered strategy."""

    name: str
    category: str
    cls: type
    config_cls: type[BaseStrategyConfig]
    description: str = ""
    tags: list[str] | None = None
    step_manifest: dict | None = None
    version: str = "1.0.0"
    strategy_api_version: str = "1.0.0"

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class StrategyRegistry:
    """Central registry for all available strategies.

    Provides registration, discovery, and instantiation capabilities.
    """

    _instance: StrategyRegistry | None = None
    _strategies: dict[str, StrategyMetadata]
    _categories: dict[str, list[str]]

    def __new__(cls) -> StrategyRegistry:
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._strategies = {}
            instance._categories = {}
            cls._instance = instance
        return cls._instance

    def register(
        self,
        name: str,
        category: str,
        cls: type,
        config_cls: type[BaseStrategyConfig],
        description: str = "",
        tags: list[str] | None = None,
        step_manifest: dict | None = None,
        version: str = "1.0.0",
        strategy_api_version: str = "1.0.0",
    ) -> None:
        """Register a strategy class."""
        if name in self._strategies:
            raise ValueError(f"Strategy '{name}' already registered")

        metadata = StrategyMetadata(
            name=name,
            category=category,
            cls=cls,
            config_cls=config_cls,
            description=description,
            tags=tags or [],
            step_manifest=step_manifest,
            version=version,
            strategy_api_version=strategy_api_version,
        )

        self._strategies[name] = metadata

        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(name)

    def get(self, name: str) -> StrategyMetadata:
        """Get strategy metadata by name."""
        if name not in self._strategies:
            available = list(self._strategies.keys())
            raise StrategyNotFoundError(name, available)
        return self._strategies[name]

    def get_class(self, name: str) -> type:
        """Get strategy class by name."""
        return self.get(name).cls

    def get_config_class(self, name: str) -> type[BaseStrategyConfig]:
        """Get strategy config class by name."""
        return self.get(name).config_cls

    def create(
        self,
        name: str,
        config: BaseStrategyConfig | dict[str, Any] | None = None,
        **kwargs,
    ) -> Any:
        """Instantiate a strategy by name with configuration."""
        metadata = self.get(name)

        if config is None:
            config = metadata.config_cls(name=name, symbol="", exchange="NSE")
        elif isinstance(config, dict):
            config = metadata.config_cls.from_dict({**config, **kwargs})
            config.name = name

        return metadata.cls(config)

    def list_strategies(
        self,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> list[str]:
        """List registered strategy names, optionally filtered."""
        names = list(self._strategies.keys())

        if category:
            names = [n for n in names if self._strategies[n].category == category]

        if tags:
            names = [n for n in names if all(t in self._strategies[n].tags for t in tags)]

        return sorted(names)

    def list_categories(self) -> list[str]:
        """List all registered categories."""
        return sorted(self._categories.keys())

    def get_category(self, category: str) -> list[str]:
        """Get all strategy names in a category."""
        return sorted(self._categories.get(category, []))

    def load_from_catalog(self, catalog_path: Path) -> None:
        """Load strategy metadata from catalog registry.json and step.toml files."""
        if not catalog_path.exists():
            return

        with catalog_path.open() as f:
            data = json.load(f)

        for entry in data.get("strategies", []):
            name = entry["name"]
            category = entry["category"]
            path_str = entry.get("path")
            if not path_str and "versions" in entry:
                latest = entry.get("latest")
                if latest and latest in entry["versions"]:
                    path_str = entry["versions"][latest]["path"]
                else:
                    path_str = next(iter(entry["versions"].values()))["path"]
            path = Path(path_str)

            # Try to import the strategy module
            try:
                mod_target = path.name if not path.name.startswith("v") else path.parent.name
                module = importlib.import_module(
                    f"honba_strategies.{category.replace('/', '.')}.{mod_target}"
                )
                cls = getattr(
                    module, "".join(w.capitalize() for w in name.split("_")) + "Strategy", None
                )
                if cls is None:
                    # Try common naming patterns
                    for attr in dir(module):
                        obj = getattr(module, attr)
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, object)
                            and attr.endswith("Strategy")
                        ):
                            cls = obj
                            break

                if cls:
                    # Try to get config class
                    config_cls = getattr(cls, "Config", None) or getattr(module, "Config", None)

                    # Load step manifest if exists
                    step_manifest = None
                    step_path = Path("catalog") / path / "step.toml"
                    if not step_path.exists():
                        step_path = catalog_path.parent / path / "step.toml"
                    if step_path.exists():
                        try:
                            import tomllib
                        except ImportError:
                            import tomli as tomllib  # type: ignore
                        with step_path.open("rb") as f:
                            step_manifest = tomllib.load(f)

                    version = "1.0.0"
                    strategy_api_version = "1.0.0"
                    if step_manifest:
                        version = step_manifest.get("version", version)
                        strategy_api_version = step_manifest.get(
                            "strategy_api_version", strategy_api_version
                        )

                    self.register(
                        name=name,
                        category=category,
                        cls=cls,
                        config_cls=config_cls or BaseStrategyConfig,
                        description=entry.get("description", ""),
                        tags=entry.get("tags", []),
                        step_manifest=step_manifest,
                        version=version,
                        strategy_api_version=strategy_api_version,
                    )
            except ImportError:
                # Strategy not yet implemented in SDK
                pass


# Global registry instance
_registry = StrategyRegistry()


def register_strategy(
    name: str,
    category: str,
    description: str = "",
    tags: list[str] | None = None,
) -> Callable[[type], type]:
    """Decorator to register a strategy class.

    Usage:
        @register_strategy("my_strategy", "execution", tags=["twap"])
        class MyStrategy:
            ...
    """

    def decorator(cls: type) -> type:
        config_cls = (
            getattr(cls, "Config", None) or getattr(cls, "config_cls", None) or BaseStrategyConfig
        )
        _registry.register(
            name=name,
            category=category,
            cls=cls,
            config_cls=config_cls,
            description=description,
            tags=tags,
        )
        return cls

    return decorator


def get_strategy(name: str) -> StrategyMetadata:
    """Get strategy metadata by name."""
    return _registry.get(name)


def get_strategy_class(name: str) -> type:
    """Get strategy class by name."""
    return _registry.get_class(name)


def create_strategy(
    name: str,
    config: BaseStrategyConfig | dict[str, Any] | None = None,
    **kwargs,
) -> Any:
    """Instantiate a strategy by name with configuration."""
    return _registry.create(name, config, **kwargs)


def list_strategies(
    category: str | None = None,
    tags: list[str] | None = None,
) -> list[str]:
    """List registered strategy names, optionally filtered."""
    return _registry.list_strategies(category, tags)


def list_categories() -> list[str]:
    """List all registered categories."""
    return _registry.list_categories()


def get_category(category: str) -> list[str]:
    """Get all strategy names in a category."""
    return _registry.get_category(category)


# Auto-discover strategies from src/honba_strategies submodules
def _auto_discover() -> None:
    """Auto-discover strategies from SDK modules."""
    modules_to_check = [
        "honba_strategies.execution",
        "honba_strategies.arbitrage",
        "honba_strategies.market_making",
        "honba_strategies.trend",
        "honba_strategies.mean_reversion",
        "honba_strategies.portfolio",
    ]

    for module_name in modules_to_check:
        try:
            module = importlib.import_module(module_name)
            for attr_name in dir(module):
                obj: Any = getattr(module, attr_name)
                if (
                    inspect.isclass(obj)
                    and hasattr(obj, "__module__")
                    and obj.__module__ == module_name
                    and attr_name.endswith("Strategy")
                    and hasattr(obj, "_registry_meta")
                ):
                    meta: dict[str, Any] = obj._registry_meta  # type: ignore[attr-defined]
                    register_strategy(
                        meta["name"],
                        meta["category"],
                        meta.get("description", ""),
                        meta.get("tags", []),
                    )(obj)
        except ImportError:
            pass


# Initialize on module load
_auto_discover()
