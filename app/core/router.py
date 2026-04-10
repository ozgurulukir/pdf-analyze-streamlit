"""Router module for page navigation."""

from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from app.core.constants import UIPages


@dataclass
class PageRoute:
    """Represents a page route configuration."""

    name: str
    render_func: Callable
    icon: Optional[str] = None
    description: Optional[str] = None


class PageRouter:
    """
    Router for handling page navigation and rendering.
    Replaces the if/elif chain in main.py with a more maintainable structure.
    """

    def __init__(self):
        """Initialize the router with registered pages."""
        self._pages: Dict[str, PageRoute] = {}

    def register(
        self,
        name: str,
        render_func: Callable,
        icon: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        Register a page with the router.

        Args:
            name: Page identifier (e.g., "Chat", "Belgeler")
            render_func: Function to call to render the page
            icon: Optional icon for the page
            description: Optional description
        """
        self._pages[name] = PageRoute(
            name=name, render_func=render_func, icon=icon, description=description
        )

    def get_page(self, name: str) -> Optional[PageRoute]:
        """
        Get a registered page by name.

        Args:
            name: Page identifier

        Returns:
            PageRoute or None if not found
        """
        return self._pages.get(name)

    def render_page(self, name: str, *args, **kwargs) -> Any:
        """
        Render a page by name.

        Args:
            name: Page identifier
            *args, **kwargs: Arguments to pass to the render function

        Returns:
            Any: Result from the render function

        Raises:
            ValueError: If page not found
        """
        page = self.get_page(name)
        if page is None:
            raise ValueError(f"Page not found: {name}")
        return page.render_func(*args, **kwargs)

    def get_page_names(self) -> list:
        """Get list of registered page names."""
        return list(self._pages.keys())

    def get_pages(self) -> Dict[str, PageRoute]:
        """Get all registered pages."""
        return self._pages.copy()


def create_router(
    chat_page_func, library_page_func, analysis_page_func, settings_page_func
) -> PageRouter:
    """
    Factory function to create and configure the router.

    Args:
        chat_page_func: Chat page render function
        library_page_func: Library page render function
        analysis_page_func: Analysis page render function
        settings_page_func: Settings page render function

    Returns:
        Configured PageRouter instance
    """
    router = PageRouter()

    # Register pages
    router.register(
        name=UIPages.CHAT,
        render_func=chat_page_func,
        icon="💬",
        description="Chat with your documents",
    )
    router.register(
        name=UIPages.DOCUMENTS,
        render_func=library_page_func,
        icon="📚",
        description="Manage your document library",
    )
    router.register(
        name=UIPages.ANALYSIS,
        render_func=analysis_page_func,
        icon="📊",
        description="Analyze document statistics",
    )
    router.register(
        name=UIPages.SETTINGS,
        render_func=settings_page_func,
        icon="⚙️",
        description="Configure application settings",
    )

    return router


def resolve_page(selected_page: str, settings: Dict[str, Any]) -> None:
    """
    Resolve and render a page based on selection.
    This replaces the if/elif chain in main.py.

    Args:
        selected_page: Name of the page to render
        settings: Settings dictionary to pass to pages
    """
    # Map page names to render functions
    # Using 'in' for partial matching to support icons in page names

    if UIPages.CHAT in selected_page:
        from app.ui.pages.chat_page import render_chat_page

        render_chat_page(settings)
    elif UIPages.DOCUMENTS in selected_page:
        from app.ui.pages.library_page import render_library_page

        render_library_page(settings)
    elif UIPages.ANALYSIS in selected_page:
        from app.ui.pages.analysis_page import render_analysis_page

        render_analysis_page()
    elif UIPages.SETTINGS in selected_page:
        from app.ui.pages.settings_page import render_settings_page

        settings.update(render_settings_page())
    else:
        # Default to chat
        from app.ui.pages.chat_page import render_chat_page

        render_chat_page(settings)
