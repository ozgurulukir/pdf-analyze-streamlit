import functools

import streamlit as st
from streamlit.runtime.scriptrunner import RerunException

from app.core.exceptions import ChromaError, DatabaseError
from app.core.logger import logger


def handle_errors(error_message: str = "İşlem sırasında bir hata oluştu.", use_alert: bool = False):
    """
    Decorator to centralize error handling for UI callbacks.
    Supports localization keys (e.g., 'messages.db_error') or direct strings.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RerunException:
                raise
            except (DatabaseError, ChromaError) as e:
                logger.error(f"Service error in {func.__name__}: {e}")
                
                # Dynamic translation lookup
                final_msg = error_message
                if "locale" in st.session_state:
                    L = st.session_state.locale
                    try:
                        # Attempt to resolve dot-notation key (e.g. settings.health_issue_sync)
                        parts = error_message.split(".")
                        obj = L
                        for part in parts:
                            obj = getattr(obj, part)
                        if isinstance(obj, str):
                            final_msg = obj
                    except (AttributeError, KeyError):
                        pass # Fallback to original string

                msg = f"{final_msg}: {str(e)}"
                if use_alert:
                    st.session_state["pending_toast"] = (msg, "❌")
                else:
                    st.error(msg)
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                
                final_msg = error_message
                if "locale" in st.session_state:
                    L = st.session_state.locale
                    try:
                        parts = error_message.split(".")
                        obj = L
                        for part in parts:
                            obj = getattr(obj, part)
                        if isinstance(obj, str):
                            final_msg = obj
                    except (AttributeError, KeyError):
                        pass

                if use_alert:
                    st.session_state["pending_toast"] = (final_msg, "❌")
                else:
                    st.error(final_msg)
        return wrapper
    return decorator
