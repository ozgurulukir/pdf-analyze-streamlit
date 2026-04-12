import functools

import streamlit as st
from streamlit.runtime.scriptrunner import RerunException

from app.core.exceptions import ChromaError, DatabaseError
from app.core.logger import logger


def handle_errors(error_message: str = "İşlem sırasında bir hata oluştu.", use_alert: bool = False):
    """
    Decorator to centralize error handling for UI callbacks.
    Args:
        error_message: Mesaj metni.
        use_alert: True ise st.session_state üzerinden toast ayarlar ve st.rerun() tetikler.
                   False ise sayfaya st.error() basar.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RerunException:
                # Streamlit'in rerun signal'ini yutmamak için
                raise
            except (DatabaseError, ChromaError) as e:
                logger.error(f"Service error in {func.__name__}: {e}")
                msg = f"{error_message}: {str(e)}"
                if use_alert:
                    st.session_state["pending_toast"] = (msg, "❌")
                else:
                    st.error(msg)
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                if use_alert:
                    st.session_state["pending_toast"] = (error_message, "❌")
                else:
                    st.error(error_message)
        return wrapper
    return decorator
