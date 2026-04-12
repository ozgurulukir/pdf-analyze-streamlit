from typing import Any

import streamlit as st

from app.core.constants import SessionKeys
from app.core.models import Workspace


class AppState:
    """Type-safe interface for st.session_state access across the application."""

    @staticmethod
    def get(key: SessionKeys | str, default: Any = None) -> Any:
        """Get a value from session state, returning default if not found."""
        k = key.value if isinstance(key, SessionKeys) else key
        return st.session_state.get(k, default)

    @staticmethod
    def set(key: SessionKeys | str, value: Any) -> None:
        """Set a value in session state."""
        k = key.value if isinstance(key, SessionKeys) else key
        st.session_state[k] = value

    @staticmethod
    def delete(key: SessionKeys | str) -> None:
        """Delete a key from session state if it exists."""
        k = key.value if isinstance(key, SessionKeys) else key
        if k in st.session_state:
            del st.session_state[k]

    @staticmethod
    def pop_toast() -> tuple[str, str] | None:
        """Retrieve and remove a pending toast from state."""
        if "pending_toast" in st.session_state and st.session_state["pending_toast"]:
            return st.session_state.pop("pending_toast")
        return None

    # --- Typed Properties ---

    @property
    def active_workspace_id(self) -> str | None:
        return self.get(SessionKeys.ACTIVE_WORKSPACE_ID)

    @active_workspace_id.setter
    def active_workspace_id(self, value: str | None):
        self.set(SessionKeys.ACTIVE_WORKSPACE_ID, value)

    @property
    def active_session_id(self) -> str | None:
        return self.get(SessionKeys.ACTIVE_SESSION_ID)

    @active_session_id.setter
    def active_session_id(self, value: str | None):
        self.set(SessionKeys.ACTIVE_SESSION_ID, value)

    @property
    def workspaces(self) -> list[Workspace]:
        return self.get(SessionKeys.WORKSPACES, [])

    @workspaces.setter
    def workspaces(self, value: list[Workspace]):
        self.set(SessionKeys.WORKSPACES, value)

    @property
    def current_page(self) -> str:
        from app.core.constants import UIPages
        return self.get(SessionKeys.CURRENT_PAGE, UIPages.CHAT)

    @current_page.setter
    def current_page(self, value: str):
        self.set(SessionKeys.CURRENT_PAGE, value)

    @property
    def locale(self):
        """Returns the current locale strings if configured in state."""
        return self.get("locale")

# Singleton instance
state = AppState()
