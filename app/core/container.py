"""Dependency injection container for application services."""

from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, TypeVar, get_type_hints

from app.core.config import AppConfig
from app.core.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class DependencyError(Exception):
    """Raised when dependency resolution fails."""

    pass


@dataclass
class Dependency:
    """Represents a registered dependency."""

    factory: Callable[..., Any]
    singleton: bool = True
    instance: Any | None = None


class Container:
    """
    Simple dependency injection container.

    Usage:
        container = Container()

        # Register dependencies
        container.register(AppConfig)
        container.register(DatabaseManager)

        # Get dependencies
        config = container.resolve(AppConfig)
        db = container.resolve(DatabaseManager)
    """

    def __init__(self):
        """Initialize the container."""
        self._dependencies: dict[str, Dependency] = {}
        self._singletons: dict[str, Any] = {}

    def register(
        self,
        interface: type[T],
        factory: Callable[..., T] | None = None,
        singleton: bool = True,
    ) -> None:
        """
        Register a dependency.

        Args:
            interface: The interface/class to register
            factory: Factory function to create the instance
            singleton: Whether to create only one instance (default: True)
        """
        name = self._get_name(interface)

        if factory is None:
            # Use the interface itself as factory
            factory = interface

        self._dependencies[name] = Dependency(factory=factory, singleton=singleton)
        logger.debug(f"Registered dependency: {name} (singleton={singleton})")

    def register_instance(self, interface: type[T], instance: T) -> None:
        """
        Register an existing instance.

        Args:
            interface: The interface/class
            instance: The instance to register
        """
        name = self._get_name(interface)
        self._dependencies[name] = Dependency(
            factory=lambda: instance, singleton=True, instance=instance
        )
        self._singletons[name] = instance
        logger.debug(f"Registered instance: {name}")

    def resolve(self, interface: type[T], *args, **kwargs) -> T:
        """
        Resolve a dependency.

        Args:
            interface: The interface/class to resolve
            *args, **kwargs: Additional arguments for the factory

        Returns:
            The resolved instance

        Raises:
            DependencyError: If dependency cannot be resolved
        """
        name = self._get_name(interface)

        if name in self._singletons:
            return self._singletons[name]

        if name not in self._dependencies:
            # Try to auto-register
            try:
                self.register(interface)
            except Exception as e:
                raise DependencyError(f"Cannot resolve {name}: {e}")

        dep = self._dependencies[name]

        # Create instance
        try:
            instance = dep.factory(*args, **kwargs)

            if dep.singleton:
                self._singletons[name] = instance

            return instance
        except Exception as e:
            raise DependencyError(f"Failed to create {name}: {e}")

    def resolve_dependencies(self, func: Callable) -> tuple:
        """
        Resolve dependencies for a function based on its type hints.

        Args:
            func: Function to analyze

        Returns:
            Tuple of resolved dependencies
        """
        type_hints = get_type_hints(func)
        return tuple(self.resolve(t) for t in type_hints.values())

    def call(self, func: Callable[T], *args, **kwargs) -> T:
        """
        Call a function with resolved dependencies.

        Args:
            func: Function to call
            *args, **kwargs: Additional arguments

        Returns:
            Function result
        """
        # Get function signature
        import inspect

        inspect.signature(func)

        # Resolve dependencies from type hints
        deps = self.resolve_dependencies(func)

        # Merge with provided args
        call_args = list(deps) + list(args)
        call_kwargs = {**kwargs}

        return func(*call_args, **call_kwargs)

    def clear(self) -> None:
        """Clear all registered dependencies."""
        self._dependencies.clear()
        self._singletons.clear()
        logger.debug("Container cleared")

    @staticmethod
    def _get_name(interface: type) -> str:
        """Get the name for an interface."""
        if hasattr(interface, "__name__"):
            return interface.__name__
        return str(interface)


# ===================
# Application Container
# ===================


class AppContainer(Container):
    """
    Application-specific container with pre-configured dependencies.
    """

    def __init__(self):
        super().__init__()
        self._configured = False

    def configure(self) -> None:
        """Configure the container with application dependencies."""
        if self._configured:
            return

        # Core configuration
        self.register(AppConfig, singleton=True)

        # Database
        from app.core.database import DatabaseManager

        self.register(DatabaseManager, singleton=True)

        # Chroma
        from app.core.chroma import ChromaManager, EmbeddingManager

        self.register(ChromaManager, singleton=True)
        self.register(EmbeddingManager, singleton=True)

        # Jobs
        from app.core.jobs import JobQueue

        self.register(JobQueue, singleton=True)

        # Services
        from app.core.services.chat_service import ChatService
        from app.core.services.file_service import FileService

        self.register(ChatService, singleton=False)
        self.register(FileService, singleton=False)

        # Health
        from app.core.health import HealthChecker

        self.register(HealthChecker, singleton=True)

        self._configured = True
        logger.info("Application container configured")

    def get_config(self) -> AppConfig:
        """Get application configuration."""
        return self.resolve(AppConfig)

    def get_database(self) -> Any:
        """Get database manager."""
        return self.resolve(DatabaseManager)

    def get_chroma(self) -> Any:
        """Get ChromaDB manager."""
        return self.resolve(ChromaManager)

    def get_embedding_manager(self) -> Any:
        """Get embedding manager."""
        return self.resolve(EmbeddingManager)


# ===================
# Global Container
# ===================

_global_container: AppContainer | None = None


def get_container() -> AppContainer:
    """Get the global application container."""
    global _global_container
    if _global_container is None:
        _global_container = AppContainer()
        _global_container.configure()
    return _global_container


def inject(func: Callable[T]) -> Callable[T]:
    """
    Decorator to inject dependencies into a function.

    Usage:
        @inject
        def my_service(config: AppConfig, db: DatabaseManager):
            ...
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        container = get_container()
        return container.call(func, *args, **kwargs)

    return wrapper


# ===================
# Service Locator Pattern
# ===================


def get_config() -> AppConfig:
    """Get application config (service locator)."""
    return get_container().get_config()


def get_database() -> Any:
    """Get database manager (service locator)."""
    return get_container().get_database()


def get_chroma() -> Any:
    """Get ChromaDB manager (service locator)."""
    return get_container().get_chroma()
